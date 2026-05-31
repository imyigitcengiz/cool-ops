"""Yol haritası muhasebe modülleri — borç, çoklu kasa, proje maliyeti, dış aktarım, zaman, projeler."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from common.permissions import accounting_fallback_redirect, can_manage_finance
from core_settings.models import (
    CashAccount,
    OperationalProject,
    SupplierPayable,
    TimeEntry,
)


def _finance_guard(view_method):
    def wrapper(self, request, *args, **kwargs):
        if not can_manage_finance(request.user):
            messages.error(request, 'Bu ekran için yetkiniz yok.')
            return accounting_fallback_redirect(request.user)
        return view_method(self, request, *args, **kwargs)
    return wrapper


class AccountingPayablesView(TemplateView):
    template_name = 'muhasebe/payables.html'

    def dispatch(self, request, *args, **kwargs):
        if not can_manage_finance(request.user):
            messages.error(request, 'Tedarikçi borçları için yetkiniz yok.')
            return accounting_fallback_redirect(request.user)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from core_settings.payables import create_payable, parse_decimal, record_payment

        action = request.POST.get('action', '')
        if action == 'create':
            try:
                amount = parse_decimal(request.POST.get('amount', '0'))
                due_raw = (request.POST.get('due_date') or '').strip()
                due_date = date.fromisoformat(due_raw) if due_raw else None
                create_payable(
                    supplier_name=request.POST.get('supplier_name', ''),
                    amount=amount,
                    due_date=due_date,
                    invoice_ref=request.POST.get('invoice_ref', ''),
                    notes=request.POST.get('notes', ''),
                )
                messages.success(request, 'Tedarikçi borcu eklendi.')
            except ValueError as exc:
                messages.error(request, str(exc))
        elif action == 'pay':
            payable = get_object_or_404(SupplierPayable, pk=request.POST.get('payable_id'))
            try:
                amount = parse_decimal(request.POST.get('pay_amount', '0'))
                record_payment(payable, amount, request.user)
                messages.success(request, 'Ödeme kaydedildi ve gider oluşturuldu.')
            except ValueError as exc:
                messages.error(request, str(exc))
        return redirect('accounting_payables')

    def get_context_data(self, **kwargs):
        from core_settings.payables import build_payables_context

        context = super().get_context_data(**kwargs)
        overdue_days = 30
        raw = self.request.GET.get('overdue_days', '')
        if raw.isdigit():
            overdue_days = max(1, int(raw))
        context.update(build_payables_context(overdue_days=overdue_days))
        return context


class AccountingCashAccountsView(TemplateView):
    template_name = 'muhasebe/cash_accounts.html'

    def dispatch(self, request, *args, **kwargs):
        if not can_manage_finance(request.user):
            messages.error(request, 'Hesap listesi için yetkiniz yok.')
            return accounting_fallback_redirect(request.user)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from core_settings.cash_accounts import create_account

        action = request.POST.get('action', '')
        if action == 'create':
            try:
                opening = Decimal(str(request.POST.get('opening_balance', '0')).replace(',', '.'))
            except InvalidOperation:
                opening = Decimal('0')
            create_account(
                name=request.POST.get('name', ''),
                account_type=request.POST.get('account_type', CashAccount.TYPE_CASH),
                opening_balance=opening,
                is_default=request.POST.get('is_default') == 'on',
            )
            messages.success(request, 'Hesap eklendi.')
        return redirect('accounting_cash_accounts')

    def get_context_data(self, **kwargs):
        from core_settings.cash_accounts import build_accounts_context

        context = super().get_context_data(**kwargs)
        context.update(build_accounts_context())
        return context


class AccountingProjectCostingView(TemplateView):
    template_name = 'muhasebe/project_costing.html'

    def dispatch(self, request, *args, **kwargs):
        if not can_manage_finance(request.user):
            messages.error(request, 'Proje maliyet ekranı için yetkiniz yok.')
            return accounting_fallback_redirect(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from core_settings.project_costing import build_project_costing_context

        context = super().get_context_data(**kwargs)
        lead_raw = self.request.GET.get('lead', '')
        lead_id = int(lead_raw) if lead_raw.isdigit() else None
        context.update(build_project_costing_context(lead_id=lead_id))
        return context


class AccountingEExportView(TemplateView):
    template_name = 'muhasebe/e_export.html'

    def dispatch(self, request, *args, **kwargs):
        if not can_manage_finance(request.user):
            messages.error(request, 'Dış aktarım için yetkiniz yok.')
            return accounting_fallback_redirect(request.user)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from core_settings.e_export import build_combined_csv, save_advisor_note

        action = request.POST.get('action', '')
        if action == 'note':
            save_advisor_note(request.POST.get('advisor_note', ''))
            messages.success(request, 'Mali müşavir notu kaydedildi.')
            return redirect('accounting_e_export')

        start_raw = (request.POST.get('start') or '').strip()
        end_raw = (request.POST.get('end') or '').strip()
        try:
            start = date.fromisoformat(start_raw)
            end = date.fromisoformat(end_raw)
        except ValueError:
            messages.error(request, 'Geçerli tarih aralığı seçin.')
            return redirect('accounting_e_export')

        csv_text = build_combined_csv(start=start, end=end)
        response = HttpResponse(csv_text, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="coolops-dis-aktarim-{start}_{end}.csv"'
        return response

    def get_context_data(self, **kwargs):
        from core_settings.e_export import build_e_export_summary

        context = super().get_context_data(**kwargs)
        start = end = None
        start_raw = self.request.GET.get('start', '')
        end_raw = self.request.GET.get('end', '')
        if start_raw and end_raw:
            try:
                start = date.fromisoformat(start_raw)
                end = date.fromisoformat(end_raw)
            except ValueError:
                pass
        context.update(build_e_export_summary(start=start, end=end))
        return context


class AccountingTimesheetView(TemplateView):
    template_name = 'muhasebe/timesheet.html'

    def dispatch(self, request, *args, **kwargs):
        if not can_manage_finance(request.user):
            messages.error(request, 'Zaman kaydı için yetkiniz yok.')
            return accounting_fallback_redirect(request.user)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from core_settings.timesheet_ops import create_time_entry

        action = request.POST.get('action', '')
        if action == 'create':
            try:
                hours = Decimal(str(request.POST.get('hours', '0')).replace(',', '.'))
                entry_date = date.fromisoformat(request.POST.get('entry_date', ''))
                create_time_entry(
                    entry_date=entry_date,
                    hours=hours,
                    description=request.POST.get('description', ''),
                    personnel_id=request.POST.get('personnel_id') or None,
                    sales_lead_id=request.POST.get('sales_lead_id') or None,
                    project_id=request.POST.get('project_id') or None,
                    billable=request.POST.get('billable') == 'on',
                    user=request.user,
                )
                messages.success(request, 'Zaman kaydı eklendi.')
            except (ValueError, InvalidOperation) as exc:
                messages.error(request, str(exc) or 'Kayıt eklenemedi.')
        elif action == 'toggle_invoiced':
            entry = get_object_or_404(TimeEntry, pk=request.POST.get('entry_id'))
            entry.invoiced = not entry.invoiced
            entry.save(update_fields=['invoiced'])
            messages.success(request, 'Faturalama durumu güncellendi.')
        year = request.POST.get('year') or timezone.localdate().year
        month = request.POST.get('month') or timezone.localdate().month
        return redirect(f'{request.path}?year={year}&month={month}')

    def get_context_data(self, **kwargs):
        from core_settings.timesheet_ops import build_timesheet_context

        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        year = int(self.request.GET.get('year', today.year))
        month = int(self.request.GET.get('month', today.month))
        context.update(build_timesheet_context(year=year, month=month))
        from core_settings.models import OperationalProject
        from sales_leads.models import SalesLead
        context['timesheet_projects'] = OperationalProject.objects.order_by('name')[:50]
        context['timesheet_sales'] = SalesLead.objects.select_related('customer').order_by('-sale_date')[:50]
        return context


class AccountingProjectsView(TemplateView):
    template_name = 'muhasebe/projects.html'

    def dispatch(self, request, *args, **kwargs):
        if not can_manage_finance(request.user):
            messages.error(request, 'Proje ekranı için yetkiniz yok.')
            return accounting_fallback_redirect(request.user)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from core_settings.operational_projects import create_project

        action = request.POST.get('action', '')
        if action == 'create':
            create_project(
                name=request.POST.get('name', ''),
                customer_id=request.POST.get('customer_id') or None,
                sales_lead_id=request.POST.get('sales_lead_id') or None,
                status=request.POST.get('status', OperationalProject.STATUS_ACTIVE),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Proje eklendi.')
        elif action == 'status':
            project = get_object_or_404(OperationalProject, pk=request.POST.get('project_id'))
            project.status = request.POST.get('status', project.status)
            project.save(update_fields=['status'])
            messages.success(request, 'Proje durumu güncellendi.')
        return redirect('accounting_projects')

    def get_context_data(self, **kwargs):
        from core_settings.operational_projects import build_projects_context
        from customers.models import Customer
        from sales_leads.models import SalesLead

        context = super().get_context_data(**kwargs)
        context.update(build_projects_context())
        context['project_customers'] = Customer.objects.order_by('name')[:100]
        context['project_sales_leads'] = SalesLead.objects.select_related('customer').order_by('-sale_date')[:50]
        return context
