"""CSV içe / dışa aktarım merkezi — Araçlar."""

from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from common.csv_import_registry import IMPORT_TYPES, user_can_import_type
from common.permissions import can_manage_finance, can_manage_payroll
from core_settings.payroll import default_report_range, period_start
from users.mixins import PermissionRequiredMixin


def _user_can_access_csv_hub(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    checks = (
        can_manage_payroll(user),
        can_manage_finance(user),
        user.has_perm_codename('sales.manage'),
        user.has_perm_codename('sales.export'),
        user.has_perm_codename('sales.reports'),
        user.has_perm_codename('contact.customers'),
        user.has_perm_codename('contact.firms'),
        user.has_perm_codename('access.tools'),
    )
    return any(checks)


class CsvExchangeHubView(PermissionRequiredMixin, TemplateView):
    template_name = 'tools/csv_hub.html'
    permission_any = True
    permission_required = (
        'access.tools', 'access.accounting', 'contact.payroll', 'accounting.finance',
        'sales.manage', 'sales.export', 'contact.customers', 'contact.firms',
    )

    def test_func(self):
        return _user_can_access_csv_hub(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        if not _user_can_access_csv_hub(request.user):
            messages.error(request, 'CSV araçları için yetkiniz yok.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        request = self.request
        today = timezone.localdate()
        period = period_start(today)
        period_str = request.GET.get('period') or period.strftime('%Y-%m')
        default_from, default_to = default_report_range()
        payroll_from = request.GET.get('payroll_from') or default_from.strftime('%Y-%m')
        payroll_to = request.GET.get('payroll_to') or default_to.strftime('%Y-%m')
        payroll_qs = f'period_from={payroll_from}&period_to={payroll_to}'
        hub = reverse('tools_csv_hub')
        open_slug = (request.GET.get('open') or '').strip()

        rows: list[dict] = []

        if user.has_perm_codename('contact.customers') and user_can_import_type(user, 'customers'):
            cfg = IMPORT_TYPES['customers']
            rows.append({
                'slug': 'customers',
                'label': cfg['label'],
                'icon': cfg['icon'],
                'color': cfg['color'],
                'hint': cfg['sample_hint'],
                'note': cfg.get('import_note', ''),
                'export_url': reverse('customer_export_csv'),
                'import_url': (
                    f"{reverse('csv_import_wizard')}?type=customers"
                    f"&next={reverse('customers')}"
                ),
                'highlight': open_slug == 'customers',
            })

        if user.has_perm_codename('contact.firms') and user_can_import_type(user, 'firms'):
            cfg = IMPORT_TYPES['firms']
            rows.append({
                'slug': 'firms',
                'label': cfg['label'],
                'icon': cfg['icon'],
                'color': 'rose',
                'hint': cfg['sample_hint'],
                'note': '',
                'export_url': reverse('contact_google_maps_export_csv'),
                'export_label': 'Liste CSV',
                'import_url': f"{reverse('csv_import_wizard')}?type=firms&next={hub}",
                'highlight': open_slug == 'firms',
            })

        can_sales = (
            user.has_perm_codename('sales.manage')
            or user.has_perm_codename('sales.export')
            or user.has_perm_codename('sales.reports')
        )
        if can_sales and user_can_import_type(user, 'sales'):
            cfg = IMPORT_TYPES['sales']
            rows.append({
                'slug': 'sales',
                'label': cfg['label'],
                'icon': cfg['icon'],
                'color': cfg['color'],
                'hint': cfg['sample_hint'],
                'note': cfg.get('import_note', ''),
                'export_url': reverse('sales_lead_export_csv') + '?format=report',
                'export_extra': ('Liste CSV', reverse('sales_lead_export_csv')),
                'import_url': f"{reverse('csv_import_wizard')}?type=sales&next={hub}",
                'highlight': open_slug == 'sales',
            })

        if can_manage_payroll(user) and user_can_import_type(user, 'payroll'):
            cfg = IMPORT_TYPES['payroll']
            rows.append({
                'slug': 'payroll',
                'label': cfg['label'],
                'icon': cfg['icon'],
                'color': cfg['color'],
                'hint': cfg['sample_hint'],
                'note': '',
                'export_url': reverse('accounting_payroll_export') + f'?{payroll_qs}',
                'export_extra': ('Hareket CSV', reverse('accounting_payroll_ledger_export') + f'?{payroll_qs}'),
                'import_url': f"{reverse('csv_import_wizard')}?type=payroll&next={hub}",
                'highlight': open_slug == 'payroll',
            })

        if can_manage_finance(user) and user_can_import_type(user, 'finance'):
            cfg = IMPORT_TYPES['finance']
            rows.append({
                'slug': 'finance',
                'label': cfg['label'],
                'icon': cfg['icon'],
                'color': cfg['color'],
                'hint': cfg['sample_hint'],
                'note': '',
                'export_url': reverse('accounting_finance_export') + f'?period={period_str}',
                'import_url': f"{reverse('csv_import_wizard')}?type=finance&next={hub}",
                'highlight': open_slug == 'finance',
            })

        from common.csv_import_diagnostics import peek_import_report

        ctx['csv_hub_rows'] = rows
        ctx['csv_wizard_url'] = reverse('csv_import_wizard')
        ctx['csv_import_report_url'] = reverse('tools_csv_import_report') if peek_import_report(request) else ''
        ctx['finance_period_str'] = period_str
        ctx['payroll_export_query'] = payroll_qs
        return ctx
