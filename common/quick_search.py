"""Hızlı arama — sayfa ve işlem indeksi."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from django.db.models import Q
from django.urls import NoReverseMatch, reverse

from common.module_runtime import (
    MODULE_PARTICLE_FALLBACK,
    is_module_installed,
    is_particle_enabled_for_nav,
    module_available_for_nav,
    module_route_allowed,
)


@dataclass(frozen=True)
class QuickSearchItem:
    title: str
    subtitle: str
    icon: str
    group: str
    url_name: str | None = None
    url: str | None = None
    keywords: tuple[str, ...] = ()
    perms_any: tuple[str, ...] = ('access.home',)
    module_slug: str | None = None
    kind: str = 'page'


def _item(
    title: str,
    subtitle: str,
    icon: str,
    group: str,
    url_name: str,
    *,
    keywords: tuple[str, ...] = (),
    perms_any: tuple[str, ...] = ('access.home',),
    module_slug: str | None = None,
    kind: str = 'page',
) -> QuickSearchItem:
    return QuickSearchItem(
        title=title,
        subtitle=subtitle,
        icon=icon,
        group=group,
        url_name=url_name,
        keywords=keywords,
        perms_any=perms_any,
        module_slug=module_slug,
        kind=kind,
    )


QUICK_SEARCH_ITEMS: tuple[QuickSearchItem, ...] = (
    _item('Ana Panel', 'Modül kısayolları', 'layout-grid', 'Genel', 'home'),
    _item('Abonelik modülleri', 'Plan tavanı içinde aç/kapa', 'puzzle', 'Genel', 'subscription_dashboard', keywords=('modül', 'abonelik', 'kurulum')),
    _item('Entegrasyon Merkezi', 'WhatsApp, toplu mesaj, medya, kazıma', 'zap', 'Genel', 'capabilities_hub'),
    _item('Bilgi bankası', 'Tanıtım yol haritası ve demo rehberi', 'book-open', 'Genel', 'introducer_knowledge_base', keywords=('tanıtım', 'demo', 'bilgi', 'rehber'), perms_any=('access.home',)),
    _item('Profil ayarları', 'Hesap ve avatar', 'user', 'Genel', 'profile_settings'),
    _item('Süper admin paneli', 'Platform denetimi', 'shield', 'Platform', 'admin_dashboard'),
    _item('Abonelik sahipleri', 'Kiracı hesapları', 'users', 'Platform', 'admin_users'),
    _item('Sistem yedekleri', 'Tam ve panel yedeği', 'database-backup', 'Platform', 'admin_system_backup'),
    _item('Abonelik & bayi yönetimi', 'Plan, panel ve franchise', 'shield-check', 'Genel', 'subscription_dashboard', keywords=('abonelik', 'bayi', 'franchise', 'plan', 'panel')),
    _item('Ekip yönetimi', 'Kullanıcılar ve roller', 'users-round', 'Genel', 'brand_team_users', keywords=('ekip', 'kullanıcı', 'rol', 'personel'), perms_any=('access.home',)),
    _item('Rehber özeti', 'Müşteri ve firma hub', 'book-user', 'Rehber', 'contact_hub', module_slug='contact', perms_any=('access.contact',)),
    _item('Müşteriler', 'Müşteri listesi', 'users', 'Rehber', 'customers', keywords=('müşteri', 'rehber'), perms_any=('access.contact', 'contact.customers_view', 'contact.customers'), module_slug='contact'),
    _item('Yeni müşteri', 'Müşteri kaydı oluştur', 'user-plus', 'Rehber', 'customer_create', keywords=('ekle', 'yeni'), perms_any=('contact.customers',), module_slug='contact', kind='action'),
    _item('Firma rehberi', 'Firma kayıtları', 'building-2', 'Rehber', 'contact_firmalar', keywords=('firma',), perms_any=('contact.firms',), module_slug='contact'),
    _item('Firma bul', 'Google Maps araması', 'map-pin', 'Rehber', 'contact_firma_bul', keywords=('maps', 'kazı'), perms_any=('contact.firms',), module_slug='integration_data_harvest'),
    _item('Ekipler', 'Saha servis ekipleri', 'users-round', 'Rehber', 'team_network', keywords=('ekip',), perms_any=('contact.teams',), module_slug='contact'),
    _item('Yardım Masası özeti', 'Durum paneli', 'layout-dashboard', 'Yardım Masası', 'dashboard', module_slug='services', perms_any=('access.services',)),
    _item('Servis kayıtları', 'Tüm servis iş emirleri', 'clipboard-list', 'Yardım Masası', 'services', keywords=('servis', 'kayıt'), perms_any=('access.services',), module_slug='services'),
    _item('Yeni servis kaydı', 'Servis aç', 'plus', 'Yardım Masası', 'service_create', keywords=('yeni', 'aç'), perms_any=('services.manage',), module_slug='services', kind='action'),
    _item('Saha planı', 'Günlük randevu takvimi', 'calendar-days', 'Yardım Masası', 'service_schedule', keywords=('takvim', 'plan'), perms_any=('access.services',), module_slug='services'),
    _item('Muhasebe özeti', 'Finans hub', 'calculator', 'Muhasebe', 'accounting_hub', module_slug='accounting', perms_any=('access.accounting',)),
    _item('Personeller', 'Saha personeli listesi', 'users', 'Rehber', 'personnel_network', keywords=('personel',), perms_any=('contact.personnel',), module_slug='contact'),
    _item('Personel yönetimi', 'Departman, ünvan, dönem özeti', 'id-card', 'Rehber', 'accounting_personnel', keywords=('personel', 'kadro'), perms_any=('contact.personnel', 'contact.payroll'), module_slug='contact'),
    _item('Maaş & avans', 'Ödeme döngüsü', 'wallet', 'Muhasebe', 'accounting_payroll', keywords=('maaş', 'avans'), perms_any=('contact.payroll',), module_slug='accounting'),
    _item('Gelir & gider', 'Ofis giderleri', 'receipt', 'Muhasebe', 'accounting_finance', keywords=('gider', 'gelir'), perms_any=('accounting.finance',), module_slug='accounting'),
    _item('Kasa', 'Nakit özeti', 'landmark', 'Muhasebe', 'accounting_cash', keywords=('kasa', 'nakit'), perms_any=('accounting.finance',), module_slug='accounting'),
    _item('Stok & reçete', 'Malzeme stoku', 'package', 'Muhasebe', 'accounting_stock', keywords=('stok', 'malzeme'), perms_any=('accounting.finance',), module_slug='accounting'),
    _item('Tedarikçi borçları', 'Vade ve ödeme', 'truck', 'Muhasebe', 'accounting_payables', keywords=('tedarik', 'borç'), perms_any=('accounting.finance',), module_slug='supplier_payables'),
    _item('Kasa & banka', 'Çoklu hesap', 'landmark', 'Muhasebe', 'accounting_cash_accounts', keywords=('banka', 'hesap'), perms_any=('accounting.finance',), module_slug='multi_cash'),
    _item('Proje kârlılığı', 'Marj raporu', 'pie-chart', 'Muhasebe', 'accounting_project_costing', keywords=('kâr', 'maliyet'), perms_any=('accounting.finance',), module_slug='project_costing'),
    _item('Dış aktarım', 'Mali müşavir CSV', 'file-badge', 'Muhasebe', 'accounting_e_export', keywords=('e-fatura', 'export'), perms_any=('accounting.finance',), module_slug='e_invoice_bridge'),
    _item('Zaman kaydı', 'Saat & faturalama', 'clock', 'Muhasebe', 'accounting_timesheet', keywords=('zaman', 'saat'), perms_any=('accounting.finance',), module_slug='timesheet'),
    _item('Montaj programı', 'Günlük kurulum planı', 'calendar-days', 'Muhasebe', 'accounting_projects', keywords=('montaj', 'proje', 'takvim', 'program'), perms_any=('accounting.finance', 'access.accounting', 'services.manage', 'contact.teams'), module_slug='projects'),
    _item('Alacaklar', 'Bekleyen tahsilat', 'hand-coins', 'Muhasebe', 'accounting_receivables', keywords=('alacak', 'tahsilat'), perms_any=('sales.reports', 'sales.manage'), module_slug='accounting'),
    _item('Satış kayıtları', 'Pipeline listesi', 'list', 'Muhasebe', 'sales_lead_list', keywords=('satış',), perms_any=('access.accounting', 'sales.manage'), module_slug='accounting'),
    _item('Yeni satış', 'Satış kaydı oluştur', 'circle-plus', 'Muhasebe', 'sales_lead_create', keywords=('yeni satış',), perms_any=('sales.manage',), module_slug='accounting', kind='action'),
    _item('Teklifler', 'Teklif listesi', 'file-text', 'Muhasebe', 'sales_quote_list', keywords=('teklif',), perms_any=('sales.manage',), module_slug='accounting'),
    _item('Yeni teklif', 'Teklif hazırla', 'file-plus', 'Muhasebe', 'sales_quote_create', keywords=('teklif',), perms_any=('sales.manage',), module_slug='accounting', kind='action'),
    _item('Raporlar', 'Maaş ve satış raporları', 'bar-chart-3', 'Muhasebe', 'accounting_reports', keywords=('rapor',), perms_any=('contact.payroll', 'sales.reports', 'accounting.finance'), module_slug='accounting'),
    _item('CSV araçları', 'İçe / dışa aktarım merkezi', 'arrow-up-down', 'Araçlar', 'tools_csv_hub', keywords=('csv', 'import', 'export', 'veri'), perms_any=('access.tools', 'contact.payroll', 'accounting.finance', 'sales.export', 'contact.customers'), module_slug='integration_csv_exchange'),
    _item('İletişim Merkezi', 'Kampanya hub', 'messages-square', 'İletişim', 'outreach_hub', module_slug='outreach', perms_any=('access.outreach',)),
    _item('Kampanyalar', 'Toplu mesaj gönderimi', 'megaphone', 'İletişim', 'outreach_campaigns', keywords=('kampanya', 'toplu mesaj'), perms_any=('access.outreach',), module_slug='integration_bulk_messaging'),
    _item('WhatsApp bağlan', 'Köprü ve senaryolar', 'message-circle', 'Araçlar', 'tools_whatsapp_baglan', keywords=('whatsapp',), perms_any=('tools.whatsapp',), module_slug='integration_whatsapp_bridge'),
    _item('Medya kütüphanesi', 'Yüklenen dosyalar', 'images', 'Araçlar', 'tools_media_library', keywords=('medya', 'dosya'), perms_any=('tools.media',), module_slug='integration_media'),
    _item('Araçlar', 'Entegrasyon kısayolları', 'hammer', 'Araçlar', 'tools_hub', keywords=('araç',), perms_any=('access.tools',)),
    _item('Site ayarları', 'Firma bilgileri', 'building-2', 'Ayarlar', 'settings_genel', keywords=('ayar', 'firma'), perms_any=('access.settings',), module_slug='settings'),
    _item('Ürün kataloğu', 'Ortak ürünler', 'package', 'Ayarlar', 'settings_products', keywords=('ürün',), perms_any=('access.settings',), module_slug='settings'),
    _item('Durumlar', 'Servis durum seçenekleri', 'list-checks', 'Ayarlar', 'settings_statuses', keywords=('durum',), perms_any=('access.settings',), module_slug='settings'),
    _item('Öncelikler', 'Servis öncelik seçenekleri', 'flag', 'Ayarlar', 'settings_priorities', keywords=('öncelik',), perms_any=('access.settings',), module_slug='settings'),
    _item('Arıza tipleri', 'Servis tip kataloğu', 'wrench', 'Ayarlar', 'settings_service_types', keywords=('arıza', 'tip'), perms_any=('access.settings',), module_slug='settings'),
    _item('Firma etiketleri', 'Rehber etiketleri', 'tags', 'Ayarlar', 'settings_tags', keywords=('etiket',), perms_any=('access.settings',), module_slug='settings'),
)


_SUPERUSER_QUICK_URLS = frozenset({
    'profile_settings',
    'admin_dashboard',
    'admin_users',
    'admin_system_backup',
})


def _user_can_see_item(user, item: QuickSearchItem, *, request=None) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if item.module_slug:
        if item.module_slug == 'settings':
            if not user.has_perm_codename('access.settings'):
                return False
        elif particle := MODULE_PARTICLE_FALLBACK.get(item.module_slug):
            if not is_particle_enabled_for_nav(particle):
                return False
            if not is_module_installed('accounting'):
                return False
        elif not module_route_allowed(item.module_slug):
            return False
        elif not module_available_for_nav(user, item.module_slug):
            return False
    if item.perms_any:
        return user.has_any_perm_codename(*item.perms_any)
    return True


def _resolve_url(item: QuickSearchItem) -> str | None:
    if item.url and isinstance(item.url, str):
        return item.url
    if not item.url_name:
        return None
    try:
        return reverse(item.url_name)
    except NoReverseMatch:
        return None


def _match_query(item: QuickSearchItem, q: str) -> bool:
    if not q:
        return True
    blob = ' '.join((item.title, item.subtitle, item.group, *item.keywords)).lower()
    return q in blob or any(part in blob for part in q.split() if len(part) >= 2)


def _query_digits(q: str) -> str:
    return ''.join(c for c in q if c.isdigit())


def _phone_variants(digits: str) -> set[str]:
    """DB'deki boşluklu/0 önekli telefon formatları için arama adayları."""
    variants = {digits}
    if len(digits) == 10:
        variants.add(f'0{digits}')
        variants.add(f'0{digits[:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}')
        variants.add(f'{digits[:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}')
    elif len(digits) == 11 and digits.startswith('0'):
        variants.add(f'{digits[:4]} {digits[4:7]} {digits[7:9]} {digits[9:11]}')
    elif len(digits) >= 12 and digits.startswith('90'):
        local = digits[2:]
        variants.update(_phone_variants(local))
    return {v for v in variants if v}


def _contact_search_q(
    q: str,
    *,
    name_prefix: str = '',
    phone_field: str = 'phone',
    phone_norm_field: str | None = None,
) -> Q:
    """İsim + telefon (ham ve normalize) ile kayıt filtresi."""
    name_lookup = f'{name_prefix}name__icontains' if name_prefix else 'name__icontains'
    phone_lookup = f'{name_prefix}{phone_field}__icontains'
    filters = Q(**{name_lookup: q}) | Q(**{phone_lookup: q})

    digits = _query_digits(q)
    if len(digits) >= 3:
        for candidate in _phone_variants(digits):
            filters |= Q(**{phone_lookup: candidate})
        from tools.phone_utils import normalize_phone

        norm = normalize_phone(q)
        if norm:
            for candidate in _phone_variants(norm):
                filters |= Q(**{phone_lookup: candidate})
                if phone_norm_field:
                    norm_lookup = f'{name_prefix}{phone_norm_field}__icontains'
                    filters |= Q(**{norm_lookup: candidate})
    return filters


def build_quick_search_results(user, query: str = '', *, limit: int = 20, request=None) -> list[dict]:
    q = (query or '').strip().lower()
    out: list[dict] = []
    for item in QUICK_SEARCH_ITEMS:
        if not _user_can_see_item(user, item, request=request):
            continue
        if q and not _match_query(item, q):
            continue
        url = _resolve_url(item)
        if not url:
            continue
        out.append({
            'title': item.title,
            'subtitle': item.subtitle,
            'url': url,
            'icon': item.icon,
            'group': item.group,
            'kind': item.kind,
        })
        if len(out) >= limit:
            break
    return out


def search_entities(user, query: str, *, limit: int = 5, request=None) -> list[dict]:
    q = (query or '').strip()
    if len(q) < 2:
        return []
    results: list[dict] = []
    per_type = max(2, limit // 2)

    if user.has_any_perm_codename('contact.customers_view', 'contact.customers'):
        from customers.models import Customer

        cust_qs = Customer.objects.filter(_contact_search_q(q)).order_by('name')
        if request:
            from common.brand_scope import filter_customers

            cust_qs = filter_customers(cust_qs, request)
        for customer in cust_qs[:per_type]:
            try:
                url = reverse('customer_update', kwargs={'pk': customer.pk})
            except NoReverseMatch:
                url = reverse('customers')
            phone = (customer.phone or '').strip()
            subtitle = phone if phone else 'Müşteri kaydı'
            results.append({
                'title': customer.name,
                'subtitle': subtitle,
                'url': url,
                'icon': 'user',
                'group': 'Kayıtlar',
                'kind': 'record',
            })

    if user.has_perm_codename('contact.firms'):
        from tools.models import MapsScrapedFirm
        from tools.outreach_memory import CUSTOMER_SHADOW_NOTE

        firm_qs = (
            MapsScrapedFirm.objects.exclude(notes=CUSTOMER_SHADOW_NOTE)
            .filter(
                _contact_search_q(q, phone_norm_field='phone_normalized')
                | Q(region__icontains=q)
                | Q(address__icontains=q),
            )
            .order_by('-last_scraped_at', 'name')
        )
        for firm in firm_qs[:per_type]:
            phone = (firm.phone or '').strip()
            try:
                base = reverse('contact_firmalar')
                url = f'{base}?{urlencode({"q": q})}'
            except NoReverseMatch:
                url = '#'
            results.append({
                'title': firm.name,
                'subtitle': phone if phone else 'Firma kaydı',
                'url': url,
                'icon': 'building-2',
                'group': 'Kayıtlar',
                'kind': 'record',
            })

    if user.has_perm_codename('access.services'):
        from services.models import ServiceRecord

        svc_qs = ServiceRecord.objects.select_related('customer').filter(
            _contact_search_q(q, name_prefix='customer__', phone_field='phone')
            | Q(customer__name__icontains=q),
        ).order_by('-updated_at')
        if request:
            from common.brand_scope import filter_services

            svc_qs = filter_services(svc_qs, request)
        remaining = max(0, limit - len(results))
        for service in svc_qs[:remaining]:
            try:
                url = reverse('service_update', kwargs={'pk': service.pk})
            except NoReverseMatch:
                url = reverse('services')
            phone = (service.customer.phone or '').strip()
            subtitle = 'Servis kaydı'
            if phone:
                subtitle = f'Servis · {phone}'
            results.append({
                'title': f'#{service.pk} · {service.customer.name}',
                'subtitle': subtitle,
                'url': url,
                'icon': 'headphones',
                'group': 'Kayıtlar',
                'kind': 'record',
            })

    return results[:limit]
