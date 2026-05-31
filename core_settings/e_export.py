"""Mali müşavir / dış muhasebe aktarım paketi."""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from core_settings.models import EExportSettings, FinanceRecord, PersonnelPayment
from sales_leads.models import SalesLead


def get_e_export_settings() -> EExportSettings:
    obj, _ = EExportSettings.objects.get_or_create(pk=1)
    return obj


def save_advisor_note(note: str) -> EExportSettings:
    settings = get_e_export_settings()
    settings.advisor_note = note.strip()
    settings.save(update_fields=['advisor_note', 'updated_at'])
    return settings


def _default_period() -> tuple[date, date]:
    today = timezone.localdate()
    start = today.replace(day=1)
    return start, today


def build_e_export_summary(*, start: date | None = None, end: date | None = None) -> dict:
    if not start or not end:
        start, end = _default_period()

    finance_income = FinanceRecord.objects.filter(
        record_type=FinanceRecord.TYPE_INCOME,
        record_date__gte=start,
        record_date__lte=end,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    finance_expense = FinanceRecord.objects.filter(
        record_type=FinanceRecord.TYPE_EXPENSE,
        record_date__gte=start,
        record_date__lte=end,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    payroll = PersonnelPayment.objects.filter(
        payment_date__gte=start,
        payment_date__lte=end,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    sales = SalesLead.objects.filter(
        sale_date__gte=start,
        sale_date__lte=end,
    ).exclude(status=SalesLead.STATUS_CANCELLED)
    sales_total = sales.aggregate(t=Sum('sale_amount'))['t'] or Decimal('0')
    sales_count = sales.count()

    return {
        'export_start': start,
        'export_end': end,
        'export_finance_income': finance_income,
        'export_finance_expense': finance_expense,
        'export_payroll': payroll,
        'export_sales_total': sales_total,
        'export_sales_count': sales_count,
        'export_settings': get_e_export_settings(),
    }


def build_combined_csv(*, start: date, end: date) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['CoolOPS — Dış muhasebe aktarım paketi'])
    writer.writerow(['Dönem', f'{start.isoformat()} — {end.isoformat()}'])
    writer.writerow([])

    writer.writerow(['--- Gelir / Gider ---'])
    writer.writerow([
        'Tarih', 'Tür', 'Kategori', 'Açıklama', 'Tutar',
        'Hesap', 'Satış ID', 'Müşteri', 'Proje', 'Not',
    ])
    for rec in FinanceRecord.objects.filter(record_date__gte=start, record_date__lte=end).select_related(
        'cash_account', 'sales_lead__customer', 'operational_project',
    ).order_by('record_date'):
        writer.writerow([
            rec.record_date.isoformat(),
            rec.get_record_type_display(),
            rec.get_category_display() if rec.category else '',
            rec.title,
            f'{rec.amount:.2f}',
            rec.cash_account.name if rec.cash_account_id else '',
            rec.sales_lead_id or '',
            rec.sales_lead.customer.name if rec.sales_lead_id else '',
            rec.operational_project.name if rec.operational_project_id else '',
            rec.notes or '',
        ])

    writer.writerow([])
    writer.writerow(['--- Satış kayıtları ---'])
    writer.writerow(['Tarih', 'Müşteri', 'Proje', 'Tutar', 'Peşinat', 'Durum'])
    for lead in SalesLead.objects.filter(sale_date__gte=start, sale_date__lte=end).select_related('customer'):
        writer.writerow([
            lead.sale_date.isoformat() if lead.sale_date else '',
            lead.customer.name,
            lead.project or lead.project_display,
            f'{(lead.sale_amount or 0):.2f}',
            f'{(lead.down_payment or 0):.2f}',
            lead.get_status_display(),
        ])

    writer.writerow([])
    writer.writerow(['--- Maaş / avans ödemeleri ---'])
    writer.writerow(['Tarih', 'Personel', 'Tür', 'Tutar'])
    for pay in PersonnelPayment.objects.filter(payment_date__gte=start, payment_date__lte=end).select_related('personnel'):
        writer.writerow([
            pay.payment_date.isoformat() if pay.payment_date else '',
            pay.personnel.name,
            pay.get_payment_type_display(),
            f'{pay.amount:.2f}',
        ])

    return buffer.getvalue()
