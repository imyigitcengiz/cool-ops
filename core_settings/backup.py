import gzip
import json
import os
import shutil
import sqlite3
from datetime import datetime
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import django
from django.conf import settings
from django.core import management
from django.db import connections, transaction
from django.http import FileResponse, HttpResponse
from django.utils import timezone

from common.security_limits import MAX_BACKUP_UPLOAD_BYTES

SQLITE_MAGIC = b'SQLite format 3\x00'

BACKUP_FORMAT_V2 = 'cool-ops-backup-v2'
BRAND_BACKUP_FORMAT_V1 = 'cool-ops-brand-backup-v1'
LEGACY_BACKUP_FORMAT_V2 = 'gy-dashboard-backup-v2'

BRAND_BACKUP_MODELS = (
    'customers.customer',
    'services.servicerecord',
)


def _applied_migrations():
    """Veritabanındaki uygulanmış migration kayıtları."""
    from django.db.migrations.recorder import MigrationRecorder

    rows = MigrationRecorder.Migration.objects.order_by('app', 'name')
    return [
        {
            'app': row.app,
            'name': row.name,
            'applied': row.applied.isoformat() if row.applied else None,
        }
        for row in rows
    ]


def _dump_fixture_json() -> list:
    """Tüm uygulama verisini fixture listesi olarak döndürür."""
    sio = StringIO()
    management.call_command(
        'dumpdata',
        stdout=sio,
        indent=2,
        natural_foreign=True,
        natural_primary=True,
        exclude=['contenttypes', 'auth.permission'],
    )
    sio.seek(0)
    return json.loads(sio.read())


def _build_backup_payload() -> dict:
    migrations = _applied_migrations()
    fixture = _dump_fixture_json()
    return {
        'format': BACKUP_FORMAT_V2,
        'created_at': timezone.now().isoformat(),
        'django_version': django.get_version(),
        'database': str(settings.DATABASES.get('default', {}).get('NAME', '')),
        'migration_count': len(migrations),
        'migrations': migrations,
        'record_count': len(fixture),
        'fixture': fixture,
    }


def _serialize_brand_fixture(brand_id: int) -> list:
    from django.apps import apps
    from django.core import serializers

    fixture = []
    for label in BRAND_BACKUP_MODELS:
        model = apps.get_model(label)
        if not hasattr(model, 'brand_id'):
            continue
        qs = model.objects.filter(brand_id=brand_id)
        if qs.exists():
            fixture.extend(json.loads(serializers.serialize('json', qs)))
    return fixture


def _backup_upload_is_allowed(filename: str) -> tuple[bool, bool]:
    """
    Yedek dosya adı — (izinli_mi, gzip_mi).
    Tarayıcılar .json.gz dosyalarını çoğu zaman yalnızca .gz olarak listeler.
    """
    name = (filename or '').lower().strip()
    if name.endswith('.json.gz') or name.endswith('.json.gzip'):
        return True, True
    if name.endswith('.gz') or name.endswith('.gzip'):
        return True, True
    if name.endswith('.json'):
        return True, False
    return False, False


def _read_uploaded_json(uploaded) -> dict | list:
    """Yüklenen .json veya .json.gz dosyasını ayrıştırır."""
    if not uploaded:
        raise ValueError('Lütfen bir dosya seçin.')
    if _upload_too_large(uploaded):
        limit_mb = MAX_BACKUP_UPLOAD_BYTES // (1024 * 1024)
        raise ValueError(f'Dosya çok büyük (en fazla {limit_mb} MB).')

    filename = uploaded.name or ''
    allowed, is_gzip = _backup_upload_is_allowed(filename)
    if not allowed:
        raise ValueError('Sadece .json veya .json.gz (gzip) yedek dosyaları içe aktarılabilir.')

    tmp_input = None
    tmp_json = None
    try:
        tmp_suffix = '.json.gz' if is_gzip else '.json'
        tmp_input = NamedTemporaryFile(delete=False, suffix=tmp_suffix)
        for chunk in uploaded.chunks():
            tmp_input.write(chunk)
        tmp_input.flush()
        tmp_input.close()

        parse_path = tmp_input.name
        if is_gzip:
            tmp_json = NamedTemporaryFile(delete=False, suffix='.json')
            with gzip.open(tmp_input.name, 'rb') as gz_file, open(tmp_json.name, 'wb') as out_file:
                shutil.copyfileobj(gz_file, out_file)
            parse_path = tmp_json.name

        with open(parse_path, 'r', encoding='utf-8') as handle:
            return json.load(handle)
    finally:
        if tmp_input and os.path.exists(tmp_input.name):
            os.unlink(tmp_input.name)
        if tmp_json and os.path.exists(tmp_json.name):
            os.unlink(tmp_json.name)


def _parse_brand_backup_payload(data) -> tuple[dict, list]:
    if not isinstance(data, dict):
        raise ValueError('Geçersiz marka yedeği — JSON nesnesi bekleniyor.')
    if data.get('format') != BRAND_BACKUP_FORMAT_V1:
        raise ValueError(
            'Tanınmayan marka yedeği formatı. cool-ops-brand-backup-v1 dosyası yükleyin.'
        )
    fixture = data.get('fixture')
    if not isinstance(fixture, list):
        raise ValueError('Marka yedeğinde fixture verisi bulunamadı.')
    return data, fixture


def _split_brand_fixture(fixture: list) -> tuple[list, list]:
    customers = []
    services = []
    for row in fixture:
        model = row.get('model') or ''
        if model == 'customers.customer':
            customers.append(row)
        elif model == 'services.servicerecord':
            services.append(row)
    return customers, services


def _fk_or_none(model, pk):
    if pk in (None, ''):
        return None
    try:
        pk = int(pk)
    except (TypeError, ValueError):
        return None
    return pk if model.objects.filter(pk=pk).exists() else None


def _fk_required(model, pk, *, label: str):
    if pk in (None, ''):
        raise ValueError(f'{label} eksik — yedek bozuk veya uyumsuz.')
    try:
        pk = int(pk)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{label} geçersiz.') from exc
    if not model.objects.filter(pk=pk).exists():
        raise ValueError(
            f'{label} (kayıt #{pk}) hedef sistemde yok. '
            'Aynı platformdan alınmış yedek kullanın veya önce durum/öncelik kataloglarını eşleştirin.'
        )
    return pk


def _filter_existing_pks(model, ids):
    if not ids:
        return []
    clean = []
    for raw in ids:
        try:
            pk = int(raw)
        except (TypeError, ValueError):
            continue
        if model.objects.filter(pk=pk).exists():
            clean.append(pk)
    return clean


def _catalog_migration_hints() -> dict:
    from core_settings.models import PriorityOption, StatusOption

    return {
        'statuses': {str(row.pk): row.name for row in StatusOption.objects.all()},
        'priorities': {str(row.pk): row.name for row in PriorityOption.objects.all()},
    }


def _hint_name(hints: dict, bucket: str, old_pk) -> str | None:
    if old_pk in (None, ''):
        return None
    names = hints.get(bucket) or {}
    return names.get(str(old_pk)) or names.get(old_pk)


def _resolve_catalog_fk(
    model,
    old_pk,
    *,
    label: str,
    migration_mode: bool,
    hints: dict,
    hint_bucket: str,
    fallback_queryset,
):
    if old_pk not in (None, ''):
        try:
            pk = int(old_pk)
        except (TypeError, ValueError) as exc:
            raise ValueError(f'{label} geçersiz.') from exc
        if model.objects.filter(pk=pk).exists():
            return pk, False
        if not migration_mode:
            raise ValueError(
                f'{label} (kayıt #{pk}) hedef sistemde yok. '
                'Aynı platformdan alınmış yedek kullanın veya migrasyon modunu açın.'
            )
        hint_name = _hint_name(hints, hint_bucket, pk)
        if hint_name:
            match = model.objects.filter(name__iexact=hint_name).first()
            if match:
                return match.pk, True
    elif not migration_mode:
        raise ValueError(f'{label} eksik — yedek bozuk veya uyumsuz.')

    fallback = fallback_queryset().order_by('pk').first()
    if fallback:
        return fallback.pk, True
    raise ValueError(f'{label} kataloğu boş — önce varsayılan durum/öncelikleri oluşturun.')


def _extract_brand_fields_from_fixture(fixture: list) -> dict:
    for row in fixture:
        if row.get('model') == 'core_settings.businessbrand':
            return dict(row.get('fields') or {})
    return {}


def create_brand_for_backup_import(
    owner,
    meta: dict,
    fixture: list,
    *,
    name: str = '',
    host_slug: str = '',
) -> 'BusinessBrand':
    """Yedek meta verisinden yeni marka oluşturur."""
    from common.brand_scope import create_brand_for_user
    from core_settings.models import BusinessBrand

    backup_fields = _extract_brand_fields_from_fixture(fixture)
    brand_name = (name or meta.get('brand_name') or backup_fields.get('name') or 'Yeni Mağaza').strip()
    slug_hint = (host_slug or meta.get('brand_slug') or backup_fields.get('slug') or '').strip()

    brand = create_brand_for_user(
        owner,
        brand_name,
        host_slug=slug_hint,
        legal_name=backup_fields.get('legal_name', '') or '',
        phone=backup_fields.get('phone', '') or '',
        bypass_plan_limit=True,
    )

    if slug_hint and slug_hint != brand.slug:
        if not BusinessBrand.objects.filter(slug=slug_hint).exclude(pk=brand.pk).exists():
            brand.slug = slug_hint
            brand.save(update_fields=['slug'])

    panel_id = meta.get('panel_id', '')
    if panel_id == 'kobipos':
        from restaurant.compat import ensure_restaurant_tenant

        ensure_restaurant_tenant(brand, owner=owner)

    return brand


def import_brand_backup_file(
    uploaded,
    brand_id: int | None = None,
    *,
    replace_existing: bool = False,
    migration_mode: bool = False,
    create_new_brand: bool = False,
    new_brand_owner_id: int | None = None,
    new_brand_name: str = '',
    new_brand_host_slug: str = '',
) -> tuple[bool, str]:
    """Marka yedeğini seçilen veya yeni oluşturulan markaya yükler."""
    from core_settings.models import BusinessBrand, PriorityOption, ProductOption, ServicePersonnel
    from core_settings.models import ServiceTypeOption, SolutionPartner, StatusOption
    from core_settings.status_defaults import ensure_default_statuses
    from customers.models import Customer
    from django.contrib.auth import get_user_model
    from services.models import ServiceRecord

    User = get_user_model()

    try:
        data = _read_uploaded_json(uploaded)
        meta, fixture = _parse_brand_backup_payload(data)
        customers_data, services_data = _split_brand_fixture(fixture)
        hints = meta.get('migration_catalog') or {}

        if create_new_brand:
            if not new_brand_owner_id:
                return False, 'Yeni mağaza için abonelik sahibi seçin.'
            owner = User.objects.filter(pk=new_brand_owner_id, is_active=True, is_superuser=False).first()
            if not owner:
                return False, 'Geçerli bir abonelik sahibi bulunamadı.'
            brand = create_brand_for_backup_import(
                owner,
                meta,
                fixture,
                name=new_brand_name,
                host_slug=new_brand_host_slug,
            )
            replace_existing = True
        else:
            if not brand_id:
                return False, 'Hedef marka seçin veya sıfırdan mağaza oluşturmayı işaretleyin.'
            brand = BusinessBrand.objects.filter(pk=brand_id, is_active=True).first()
            if not brand:
                return False, 'Hedef marka bulunamadı veya pasif.'

        source_name = meta.get('brand_name') or meta.get('brand_slug') or 'bilinmeyen'
        backup_date = (meta.get('created_at') or '')[:19]
        catalog_remapped = 0

        with transaction.atomic():
            if replace_existing:
                Customer.objects.filter(brand_id=brand.pk).delete()

            customer_map: dict[int, int] = {}
            imported_customers = 0
            imported_services = 0

            for row in customers_data:
                fields = dict(row.get('fields') or {})
                old_pk = row.get('pk')
                fields.pop('brand', None)
                product_ids = _filter_existing_pks(ProductOption, fields.pop('products', []) or [])

                customer = Customer(
                    brand=brand,
                    name=fields.get('name') or '',
                    phone=fields.get('phone'),
                    region=fields.get('region'),
                    address=fields.get('address'),
                    location_link=fields.get('location_link'),
                    contract_date=fields.get('contract_date'),
                )
                customer.save()
                if product_ids:
                    customer.products.set(product_ids)
                if old_pk is not None:
                    customer_map[int(old_pk)] = customer.pk
                imported_customers += 1

            ensure_default_statuses()

            for row in services_data:
                fields = dict(row.get('fields') or {})
                old_customer_id = fields.get('customer')
                if old_customer_id is None:
                    continue
                try:
                    old_customer_id = int(old_customer_id)
                except (TypeError, ValueError):
                    continue
                new_customer_id = customer_map.get(old_customer_id)
                if not new_customer_id:
                    continue

                product_ids = _filter_existing_pks(ProductOption, fields.pop('products', []) or [])
                service_type_ids = _filter_existing_pks(
                    ServiceTypeOption, fields.pop('service_types', []) or [],
                )

                status_id, remapped = _resolve_catalog_fk(
                    StatusOption,
                    fields.get('status'),
                    label='Durum',
                    migration_mode=migration_mode,
                    hints=hints,
                    hint_bucket='statuses',
                    fallback_queryset=StatusOption.objects.all,
                )
                if remapped:
                    catalog_remapped += 1
                priority_id, remapped_p = _resolve_catalog_fk(
                    PriorityOption,
                    fields.get('priority'),
                    label='Öncelik',
                    migration_mode=migration_mode,
                    hints=hints,
                    hint_bucket='priorities',
                    fallback_queryset=PriorityOption.objects.all,
                )
                if remapped_p:
                    catalog_remapped += 1

                service = ServiceRecord(
                    brand=brand,
                    customer_id=new_customer_id,
                    status_id=status_id,
                    priority_id=priority_id,
                    solution_partner_id=_fk_or_none(SolutionPartner, fields.get('solution_partner')),
                    notes=fields.get('notes'),
                    assigned_to_id=_fk_or_none(User, fields.get('assigned_to')),
                    service_personnel_id=_fk_or_none(ServicePersonnel, fields.get('service_personnel')),
                    warranty_status=fields.get('warranty_status') or 'active',
                    partner_fee=fields.get('partner_fee'),
                    warranty_note=fields.get('warranty_note'),
                    list_price=fields.get('list_price'),
                    discounted_price=fields.get('discounted_price'),
                    scheduled_at=fields.get('scheduled_at'),
                )
                service.save()
                if product_ids:
                    service.products.set(product_ids)
                if service_type_ids:
                    service.service_types.set(service_type_ids)
                imported_services += 1

        mode = 'değiştirildi' if replace_existing else 'eklendi'
        date_note = f' Yedek tarihi: {backup_date}.' if backup_date else ''
        created_note = ' Yeni mağaza oluşturuldu.' if create_new_brand else ''
        migration_note = ''
        if migration_mode:
            migration_note = ' Migrasyon modu: kataloglar ada göre eşleştirildi.'
            if catalog_remapped:
                migration_note += f' ({catalog_remapped} alan yedekten çözümlendi)'
        return True, (
            f'"{brand.name}" markasına "{source_name}" yedeği yüklendi ({mode}): '
            f'{imported_customers} müşteri, {imported_services} servis.{created_note}{migration_note}{date_note} '
            'Not: Müşteri dosyaları (media/) bu yedekte yer almaz.'
        )
    except ValueError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f'Marka yedeği içe aktarılamadı: {exc}'


def export_brand_backup_response(brand_id: int) -> HttpResponse:
    from core_settings.models import BusinessBrand

    brand = BusinessBrand.objects.filter(pk=brand_id, is_active=True).first()
    if not brand:
        raise ValueError('Panel bulunamadı.')

    from django.core import serializers as dj_serializers

    from common.brand_panel_meta import resolve_brand_panel_meta

    fixture = _serialize_brand_fixture(brand.pk)
    brand_meta = json.loads(dj_serializers.serialize('json', [brand]))
    panel_meta = resolve_brand_panel_meta(brand)

    payload = {
        'format': BRAND_BACKUP_FORMAT_V1,
        'created_at': timezone.now().isoformat(),
        'django_version': django.get_version(),
        'brand_id': brand.pk,
        'brand_name': brand.name,
        'brand_slug': brand.slug,
        'panel_id': panel_meta.get('panel_id', ''),
        'panel_name': panel_meta.get('panel_name', ''),
        'migration_catalog': _catalog_migration_hints(),
        'record_count': len(fixture) + len(brand_meta),
        'fixture': brand_meta + fixture,
    }
    raw_json = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    safe_slug = brand.slug[:40] or str(brand.pk)
    file_name = f'cool-ops-panel-{safe_slug}-{ts}.json.gz'
    response = HttpResponse(gzip.compress(raw_json), content_type='application/gzip')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response


def export_backup_response() -> HttpResponse:
    payload = _build_backup_payload()
    raw_json = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    file_name = f'cool-ops-backup-{ts}.json.gz'
    response = HttpResponse(gzip.compress(raw_json), content_type='application/gzip')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response


def _parse_backup_file(path: str, *, is_gzip: bool) -> tuple[dict | None, list]:
    """(meta, fixture) — meta None ise eski düz fixture listesi."""
    if is_gzip:
        with gzip.open(path, 'rt', encoding='utf-8') as handle:
            data = json.load(handle)
    else:
        with open(path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
    return _parse_backup_file_from_data(data)


def _write_fixture_temp(fixture: list) -> str:
    tmp = NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8')
    json.dump(fixture, tmp, ensure_ascii=False, indent=2)
    tmp.flush()
    tmp.close()
    return tmp.name


def _run_migrations():
    management.call_command('migrate', '--noinput', verbosity=0)


def _prepare_database_for_fixture_load():
    """
    migrate sonrası migration/seed ile oluşan izinleri kaldırır.
    loaddata yedekteki Permission kayıtlarını UNIQUE codename hatası olmadan yükler.
    """
    from users.models import Permission

    Permission.objects.all().delete()


def _flush_database_for_full_restore():
    """JSON yedeği mevcut verinin üzerine karıştırmadan tam yüklemek için tabloları boşaltır."""
    _close_db_connections()
    management.call_command('flush', '--noinput', verbosity=0)


def _data_counts_summary() -> str:
    from customers.models import Customer, CustomerMedia
    from services.models import ServiceRecord, ServiceImage
    from sales_leads.models import SalesLead

    parts = [
        f'{Customer.objects.count()} müşteri',
        f'{ServiceRecord.objects.count()} servis',
        f'{SalesLead.objects.count()} satış',
        f'{CustomerMedia.objects.count()} medya kaydı',
        f'{ServiceImage.objects.count()} servis görseli',
    ]
    return ', '.join(parts)


def _sync_permissions_after_restore():
    try:
        management.call_command('sync_permissions', verbosity=0)
    except Exception:
        pass


def _upload_too_large(uploaded) -> bool:
    size = getattr(uploaded, 'size', None)
    if size is not None and size > MAX_BACKUP_UPLOAD_BYTES:
        return True
    return False


def import_backup_file(uploaded) -> tuple[bool, str]:
    tmp_fixture = None
    try:
        data = _read_uploaded_json(uploaded)
        if isinstance(data, list):
            meta, fixture = None, data
        elif isinstance(data, dict) and data.get('format') == BRAND_BACKUP_FORMAT_V1:
            return False, (
                'Bu dosya marka yedeği formatında. '
                'Marka yedeği bölümünden hedef markayı seçerek içe aktarın.'
            )
        else:
            meta, fixture = _parse_backup_file_from_data(data)
        tmp_fixture = _write_fixture_temp(fixture)

        # migrate transaction dışında (SQLite ve PostgreSQL uyumluluğu)
        _run_migrations()
        _flush_database_for_full_restore()
        _prepare_database_for_fixture_load()
        with transaction.atomic():
            management.call_command('loaddata', tmp_fixture, verbosity=0)

        _sync_permissions_after_restore()
        counts = _data_counts_summary()
        media_note = (
            ' Yüklenen dosyalar (resim/belge) media/ klasöründe — '
            'sunucuda /data/media kopyalanmadıysa medya kırık görünür.'
        )

        if meta:
            mig_count = meta.get('migration_count', len(meta.get('migrations', [])))
            rec_count = meta.get('record_count', len(fixture))
            created = meta.get('created_at', '')
            return True, (
                f'JSON yedek tam yüklendi (fixture: {rec_count} kayıt; DB: {counts}). '
                f'Migration senkronu tamamlandı ({mig_count} migration kaydı yedekte). '
                f'{f"Yedek tarihi: {created[:19]}." if created else ""}'
                f'{media_note}'
            ).strip()

        return True, (
            f'JSON yedek yüklendi (fixture: {len(fixture)} kayıt; DB: {counts}).'
            f'{media_note}'
        )
    except ValueError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f'İçe aktarma sırasında hata oluştu: {exc}'
    finally:
        if tmp_fixture and os.path.exists(tmp_fixture):
            os.unlink(tmp_fixture)


def _parse_backup_file_from_data(data) -> tuple[dict | None, list]:
    if isinstance(data, list):
        return None, data
    if isinstance(data, dict) and data.get('format') in (BACKUP_FORMAT_V2, LEGACY_BACKUP_FORMAT_V2):
        fixture = data.get('fixture')
        if not isinstance(fixture, list):
            raise ValueError('Yedek dosyasında fixture verisi bulunamadı.')
        return data, fixture
    if isinstance(data, dict) and 'fixture' in data:
        fixture = data.get('fixture')
        if isinstance(fixture, list):
            return data, fixture
    raise ValueError('Tanınmayan yedek dosyası formatı.')


def database_path() -> Path:
    return Path(settings.DATABASES['default']['NAME']).resolve()


def _close_db_connections():
    connections.close_all()


def _validate_sqlite_file(path: str | Path) -> None:
    path = Path(path)
    if path.stat().st_size < 100:
        raise ValueError('Dosya çok küçük veya boş.')
    with open(path, 'rb') as handle:
        if handle.read(16) != SQLITE_MAGIC:
            raise ValueError('Geçerli bir SQLite veritabanı dosyası değil (db.sqlite3 bekleniyor).')
    try:
        conn = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
        conn.execute('PRAGMA schema_version')
        conn.close()
    except sqlite3.DatabaseError as exc:
        raise ValueError(f'SQLite dosyası okunamadı: {exc}') from exc


def _remove_sqlite_sidecars(db_path: Path) -> None:
    for suffix in ('-wal', '-journal', '-shm'):
        sidecar = Path(f'{db_path}{suffix}')
        if sidecar.exists():
            sidecar.unlink()


def _backup_existing_db(db_path: Path) -> str | None:
    if not db_path.is_file():
        return None
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = db_path.with_name(f'{db_path.name}.bak-{ts}')
    shutil.copy2(db_path, backup_path)
    return str(backup_path)


def export_sqlite_response() -> HttpResponse:
    db_path = database_path()
    if not db_path.is_file():
        raise FileNotFoundError('Veritabanı dosyası bulunamadı.')

    _close_db_connections()
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f'cool-ops-{ts}.sqlite3'
    response = FileResponse(
        open(db_path, 'rb'),
        as_attachment=True,
        filename=filename,
        content_type='application/x-sqlite3',
    )
    response['Content-Length'] = db_path.stat().st_size
    return response


def import_sqlite_file(uploaded) -> tuple[bool, str]:
    if not uploaded:
        return False, 'Lütfen bir db.sqlite3 dosyası seçin.'
    if _upload_too_large(uploaded):
        limit_mb = MAX_BACKUP_UPLOAD_BYTES // (1024 * 1024)
        return False, f'Dosya çok büyük (en fazla {limit_mb} MB).'

    name = (uploaded.name or '').lower()
    if not (name.endswith('.sqlite3') or name.endswith('.db')):
        return False, 'Sadece .sqlite3 veya .db dosyası yüklenebilir.'

    db_path = database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = None
    try:
        tmp = NamedTemporaryFile(delete=False, suffix='.sqlite3')
        tmp_path = tmp.name
        for chunk in uploaded.chunks():
            tmp.write(chunk)
        tmp.flush()
        tmp.close()

        _validate_sqlite_file(tmp_path)

        _close_db_connections()
        prev_backup = _backup_existing_db(db_path)
        _remove_sqlite_sidecars(db_path)

        shutil.copy2(tmp_path, db_path)
        try:
            os.chmod(db_path, 0o644)
        except OSError:
            pass
        _remove_sqlite_sidecars(db_path)
        _close_db_connections()

        _run_migrations()
        _sync_permissions_after_restore()

        size_mb = db_path.stat().st_size / (1024 * 1024)
        counts = _data_counts_summary()
        msg = (
            f'SQLite yüklendi ({size_mb:.1f} MB → {db_path}). '
            f'Veritabanı: {counts}. Migration kontrolü tamamlandı.'
        )
        if prev_backup:
            msg += f' Önceki DB yedeklendi: {prev_backup}'
        msg += (
            ' ÖNEMLİ: Resim/belgeler db.sqlite3 içinde değil; lokal media/ klasörünü '
            'sunucuda /data/media (volume) içine kopyalamazsan dosyalar açılmaz.'
        )
        return True, msg
    except Exception as exc:
        return False, f'SQLite içe aktarma hatası: {exc}'
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        _close_db_connections()


def backup_status_summary() -> dict:
    migrations = _applied_migrations()
    db_path = database_path()
    db_size = db_path.stat().st_size if db_path.is_file() else 0
    return {
        'migration_count': len(migrations),
        'migrations': migrations[-8:],  # son 8 satır önizleme
        'format_version': BACKUP_FORMAT_V2,
        'database_path': str(db_path),
        'database_size': db_size,
        'database_size_display': (
            f'{db_size / (1024 * 1024):.1f} MB' if db_size >= 1024 * 1024
            else f'{db_size / 1024:.1f} KB' if db_size else '—'
        ),
        'database_exists': db_path.is_file(),
    }


FACTORY_RESET_CONFIRM_PHRASE = 'SIFIRLA'


def _seed_factory_defaults():
    from core_settings.models import SiteSettings, WorkSchedulePlan
    from core_settings.status_defaults import ensure_default_statuses
    from core_settings.work_schedule import default_weekly_hours, set_default_plan

    ensure_default_statuses()
    if not SiteSettings.objects.exists():
        SiteSettings.objects.create(site_name='Kobi Hub')
    if not WorkSchedulePlan.objects.exists():
        plan = WorkSchedulePlan.objects.create(
            name='Standart mesai',
            is_default=True,
            is_active=True,
            weekly_hours=default_weekly_hours(),
        )
        set_default_plan(plan)
    try:
        from chat.services import ensure_team_thread
        ensure_team_thread()
    except Exception:
        pass


def factory_reset_database(*, backup_before: bool = True) -> tuple[bool, str]:
    """
    Tüm uygulama verisini siler; roller, varsayılan katalog ve admin/admin hesabını yeniden kurar.
    Medya dosyalarına dokunmaz.
    """
    db_path = database_path()
    prev_backup = None
    if backup_before and db_path.is_file():
        prev_backup = _backup_existing_db(db_path)

    _close_db_connections()
    _flush_database_for_full_restore()
    _run_migrations()
    management.call_command('sync_permissions', '--reset-system-roles', verbosity=0)
    management.call_command('ensure_superadmin', '--reset-password', verbosity=0)
    _seed_factory_defaults()

    msg = (
        'Veritabanı sıfırlandı. Tüm kayıtlar silindi; varsayılan katalog ve roller yeniden oluşturuldu. '
        'Giriş: admin / admin — hemen şifrenizi değiştirin. '
        'Not: Yüklenen dosyalar (media/) silinmedi.'
    )
    if prev_backup:
        msg += f' Önceki veritabanı yedeklendi: {prev_backup}'
    return True, msg
