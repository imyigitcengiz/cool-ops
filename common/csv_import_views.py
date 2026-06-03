"""CSV içe aktarma sihirbazı — önizleme, sütun eşleştirme, içe aktarma."""

from __future__ import annotations

import json
import secrets
import time

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from common.csv_import_registry import (
    import_type_config,
    import_type_fields,
    list_import_types_for_user,
    user_can_import_sales_with_customers,
    user_can_import_type,
)
from common.csv_import_diagnostics import (
    mapping_plan_rows,
    peek_import_report,
    pop_import_report,
    store_import_report,
)
from common.csv_import_runner import prepare_import_rows, run_import
from common.csv_io import read_csv_text
from users.mixins import PermissionRequiredMixin

SESSION_PREFIX = 'csv_imp_'
SESSION_TTL = 3600
MAX_ROWS = 2000


def _session_key(token: str) -> str:
    return f'{SESSION_PREFIX}{token}'


def _store_session(request, *, import_type: str, headers: list[str], rows: list[dict]) -> str:
    token = secrets.token_urlsafe(16)
    request.session[_session_key(token)] = {
        'type': import_type,
        'headers': headers,
        'rows': rows[:MAX_ROWS],
        'expires': time.time() + SESSION_TTL,
    }
    request.session.modified = True
    return token


def _load_session(request, token: str) -> dict | None:
    if not token:
        return None
    payload = request.session.get(_session_key(token))
    if not payload:
        return None
    if payload.get('expires', 0) < time.time():
        del request.session[_session_key(token)]
        return None
    return payload


def _clear_session(request, token: str) -> None:
    key = _session_key(token)
    if key in request.session:
        del request.session[key]


def _safe_next_url(request, fallback: str) -> str:
    nxt = (request.GET.get('next') or request.POST.get('next') or '').strip()
    if nxt.startswith('/') and not nxt.startswith('//'):
        return nxt
    return fallback


def _result_message(import_type: str, result: dict) -> str:
    created = result.get('created', 0)
    updated = result.get('updated', 0)
    skipped = result.get('skipped', 0)
    cfg = import_type_config(import_type) or {}
    label = cfg.get('label', import_type)
    parts = [f'{label}: {created} kayıt eklendi.']
    if updated:
        parts.append(f'{updated} güncellendi.')
    if skipped:
        parts.append(f'{skipped} satır atlandı.')
    if result.get('products_linked'):
        parts.append(f'{result["products_linked"]} kayıtta ürün bağlandı.')
    if import_type == 'customers' and (result.get('created') or result.get('updated')):
        parts.append('Rehberde görmek için doğru marka seçili olduğundan emin olun.')
    if result.get('sales_created'):
        parts.append(f'{result["sales_created"]} satış kaydı eklendi.')
    if result.get('interim_payments'):
        parts.append(f'{result["interim_payments"]} ara ödeme kaydı eklendi.')
    if (
        result.get('created') == 0
        and result.get('updated') == 0
        and not result.get('sales_created')
        and not result.get('skipped')
    ):
        parts.append('Kayıt eklenmedi — sütun eşleştirmesini kontrol edin.')
    if result.get('unmapped_columns'):
        parts.append(f'{len(result["unmapped_columns"])} CSV sütunu kullanılmadı.')
    if result.get('warnings'):
        parts.append(f'{len(result["warnings"])} uyarı.')
    return ' '.join(parts)


def _flash_import_report(request, result: dict, *, next_url: str) -> None:
    store_import_report(request, result)
    report_url = reverse('tools_csv_import_report')
    messages.info(
        request,
        format_html(
            'Ayrıntılı içe aktarma raporu hazır — <a href="{}" class="font-bold underline">raporu açın</a>.',
            f'{report_url}?next={next_url}',
        ),
    )


def _fields_payload(import_type: str, user=None) -> list[dict]:
    return [
        {'key': f.key, 'label': f.label, 'required': f.required}
        for f in import_type_fields(import_type, user)
    ]


class CsvImportWizardView(PermissionRequiredMixin, TemplateView):
    template_name = 'common/csv_import_wizard.html'
    permission_any = True
    permission_required = (
        'access.accounting', 'contact.payroll', 'accounting.finance',
        'sales.manage', 'sales.export', 'contact.customers', 'contact.firms',
    )

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        import_type = (self.request.GET.get('type') or self.request.POST.get('type') or '').strip()
        if import_type:
            return user_can_import_type(user, import_type)
        return bool(list_import_types_for_user(user))

    def dispatch(self, request, *args, **kwargs):
        self.import_type = (request.GET.get('type') or request.POST.get('type') or '').strip()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['import_type'] = self.import_type
        ctx['import_types'] = list_import_types_for_user(self.request.user)
        ctx['next_url'] = _safe_next_url(
            self.request,
            reverse(import_type_config(self.import_type)['redirect_name']) if self.import_type else reverse('tools_csv_hub'),
        )
        if self.import_type:
            cfg = import_type_config(self.import_type)
            ctx['import_label'] = cfg['label']
            ctx['import_model'] = cfg.get('model', '')
            ctx['import_hint'] = cfg.get('sample_hint', '')
            ctx['import_note'] = cfg.get('import_note', '')
            ctx['import_interim_help'] = bool(cfg.get('import_interim_help'))
            if ctx['import_interim_help']:
                from sales_leads.csv_interim import INTERIM_IMPORT_HELP

                ctx['interim_import_help_text'] = INTERIM_IMPORT_HELP
            ctx['import_fields'] = _fields_payload(self.import_type, self.request.user)
            ctx['import_includes_sales'] = (
                self.import_type == 'customers'
                and user_can_import_sales_with_customers(self.request.user)
            )
            token = self.request.GET.get('token', '')
            payload = _load_session(self.request, token)
            if payload and payload.get('type') == self.import_type:
                ctx['preview_token'] = token
                ctx['csv_headers'] = payload['headers']
                ctx['preview_matrix'] = [
                    [row.get(h, '') for h in payload['headers']]
                    for row in payload['rows']
                ]
                ctx['row_count'] = len(payload['rows'])
                fields = list(import_type_fields(self.import_type, self.request.user))
                _, final_map, sources, auto_mapping = prepare_import_rows(
                    payload['rows'][:1],
                    payload['headers'],
                    self.import_type,
                    use_auto_mapping=True,
                    user=self.request.user,
                )
                ctx['auto_mapping'] = auto_mapping
                sample_row = payload['rows'][0] if payload['rows'] else {}
                ctx['mapping_rows'] = mapping_plan_rows(
                    fields,
                    final_mapping=final_map,
                    mapping_sources=sources,
                    auto_mapping=auto_mapping,
                    sample_row=sample_row,
                )
                from common.csv_import_diagnostics import unmapped_csv_columns

                ctx['unmapped_csv_columns'] = unmapped_csv_columns(
                    payload['headers'],
                    final_map,
                )
                if ctx.get('import_interim_help'):
                    from sales_leads.csv_interim import (
                        INTERIM_IMPORT_HELP,
                        detect_interim_headers,
                        has_interim_columns,
                    )

                    ctx['interim_import_help_text'] = INTERIM_IMPORT_HELP
                    ctx['interim_csv_columns'] = detect_interim_headers(payload['headers'])
                    ctx['interim_columns_detected'] = has_interim_columns(payload['headers'])
        return ctx

    def post(self, request, *args, **kwargs):
        import_type = (request.POST.get('type') or '').strip()
        if not user_can_import_type(request.user, import_type):
            messages.error(request, 'Bu CSV türü için yetkiniz yok.')
            return redirect('tools_csv_hub')

        step = request.POST.get('step', 'upload')
        next_url = _safe_next_url(request, reverse(import_type_config(import_type)['redirect_name']))

        if step == 'upload':
            uploaded = request.FILES.get('file')
            if not uploaded:
                messages.error(request, 'CSV dosyası seçin.')
                return redirect(f'{reverse("csv_import_wizard")}?type={import_type}&next={next_url}')
            raw = uploaded.read()
            if raw.startswith(b'\xef\xbb\xbf'):
                raw = raw[3:]
            text = raw.decode('utf-8-sig', errors='replace')
            headers, rows = read_csv_text(text)
            if not rows:
                messages.error(request, 'CSV dosyasında veri satırı bulunamadı.')
                return redirect(f'{reverse("csv_import_wizard")}?type={import_type}&next={next_url}')
            token = _store_session(request, import_type=import_type, headers=headers, rows=rows)
            return redirect(f'{reverse("csv_import_wizard")}?type={import_type}&token={token}&next={next_url}')

        if step == 'import':
            token = request.POST.get('token', '')
            payload = _load_session(request, token)
            if not payload or payload.get('type') != import_type:
                messages.error(request, 'Önizleme oturumu süresi doldu. Dosyayı tekrar yükleyin.')
                return redirect(f'{reverse("csv_import_wizard")}?type={import_type}&next={next_url}')

            from common.csv_import_registry import import_type_fields
            from common.csv_mapping import encode_mapping_headers

            mapping = {}
            for field in import_type_fields(import_type, request.user):
                vals = [v.strip() for v in request.POST.getlist(f'map_{field.key}') if v.strip()]
                mapping[field.key] = encode_mapping_headers(vals) or ''

            use_auto = request.POST.get('use_auto_mapping') == '1'
            _, final_map, _, _ = prepare_import_rows(
                payload['rows'][:1],
                payload['headers'],
                import_type,
                mapping=mapping,
                use_auto_mapping=use_auto,
                user=request.user,
            )
            from common.csv_mapping import mapping_headers

            if import_type == 'customers' and not mapping_headers(final_map.get('name')):
                messages.error(
                    request,
                    'Müşteri Adı sütunu eşleştirilmedi. CSV başlığını «Müşteri Adı» ile eşleştirin.',
                )
                return redirect(
                    f'{reverse("csv_import_wizard")}?type={import_type}&token={token}&next={next_url}'
                )

            try:
                result = run_import(
                    import_type,
                    payload['rows'],
                    user=request.user,
                    request=request,
                    raw_rows=payload['rows'],
                    mapping=mapping,
                    headers=payload['headers'],
                    use_auto_mapping=use_auto,
                )
                _clear_session(request, token)
                messages.success(request, _result_message(import_type, result))
                if result.get('skipped'):
                    messages.warning(
                        request,
                        f'{result["skipped"]} satır atlandı — ayrıntılar raporda.',
                    )
                _flash_import_report(request, result, next_url=next_url)
            except Exception as exc:
                messages.error(request, f'İçe aktarma başarısız: {exc}')
            return redirect(next_url)

        return redirect(f'{reverse("csv_import_wizard")}?type={import_type}&next={next_url}')


class CsvImportReportView(PermissionRequiredMixin, TemplateView):
    """Son içe aktarma — atlanan satırlar, uyarılar, kullanılmayan sütunlar."""

    template_name = 'tools/csv_import_report.html'
    permission_any = True
    permission_required = (
        'access.accounting', 'contact.payroll', 'accounting.finance',
        'sales.manage', 'sales.export', 'contact.customers', 'contact.firms',
    )

    def test_func(self):
        return self.request.user.is_authenticated

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report = pop_import_report(self.request)
        if not report:
            messages.info(self.request, 'Görüntülenecek içe aktarma raporu yok.')
            return ctx
        cfg = import_type_config(report.get('import_type', '')) or {}
        ctx['report'] = report
        ctx['report_label'] = cfg.get('label', report.get('import_type', 'İçe aktarma'))
        ctx['next_url'] = _safe_next_url(self.request, reverse('tools_csv_hub'))
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if not peek_import_report(request):
            return redirect(_safe_next_url(request, reverse('tools_csv_hub')))
        return super().dispatch(request, *args, **kwargs)


@require_http_methods(['POST'])
def csv_import_preview_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Oturum gerekli.'}, status=401)

    import_type = (request.POST.get('type') or '').strip()
    if not user_can_import_type(request.user, import_type):
        return JsonResponse({'ok': False, 'error': 'Yetkiniz yok.'}, status=403)

    uploaded = request.FILES.get('file')
    if not uploaded:
        return JsonResponse({'ok': False, 'error': 'CSV dosyası seçin.'}, status=400)

    raw = uploaded.read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    text = raw.decode('utf-8-sig', errors='replace')
    headers, rows = read_csv_text(text)
    if not rows:
        return JsonResponse({'ok': False, 'error': 'Veri satırı yok.'}, status=400)

    token = _store_session(request, import_type=import_type, headers=headers, rows=rows)
    _, _, _, auto_mapping = prepare_import_rows(
        rows[:1], headers, import_type, user=request.user,
    )
    return JsonResponse({
        'ok': True,
        'token': token,
        'headers': headers,
        'fields': _fields_payload(import_type, request.user),
        'auto_mapping': auto_mapping,
        'preview_rows': rows[:MAX_ROWS],
        'row_count': len(rows),
    })


@require_http_methods(['POST'])
def csv_import_execute_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Oturum gerekli.'}, status=401)

    import_type = (request.POST.get('type') or '').strip()
    if not user_can_import_type(request.user, import_type):
        return JsonResponse({'ok': False, 'error': 'Yetkiniz yok.'}, status=403)

    token = request.POST.get('token', '')
    payload = _load_session(request, token)
    if not payload or payload.get('type') != import_type:
        return JsonResponse({'ok': False, 'error': 'Oturum süresi doldu.'}, status=400)

    mapping_raw = request.POST.get('mapping', '{}')
    try:
        mapping = json.loads(mapping_raw)
    except json.JSONDecodeError:
        mapping = {}

    try:
        result = run_import(
            import_type,
            payload['rows'],
            user=request.user,
            raw_rows=payload['rows'],
            mapping=mapping,
            headers=payload['headers'],
        )
        _clear_session(request, token)
        return JsonResponse({'ok': True, 'result': result, 'message': _result_message(import_type, result)})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
