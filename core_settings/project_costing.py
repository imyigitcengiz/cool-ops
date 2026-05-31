"""Proje maliyet ve kârlılık — satış geliri vs gider."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum

from core_settings.models import FinanceRecord
from sales_leads.models import SalesLead


def _lead_revenue(lead: SalesLead) -> Decimal:
    return lead.sale_amount or Decimal('0')


def _lead_collected(lead: SalesLead) -> Decimal:
    return (lead.down_payment or Decimal('0')) + lead.interim_payments_total


def _lead_expenses(lead: SalesLead) -> Decimal:
    return FinanceRecord.objects.filter(
        sales_lead=lead,
        record_type=FinanceRecord.TYPE_EXPENSE,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')


def build_costing_row(lead: SalesLead) -> dict:
    revenue = _lead_revenue(lead)
    collected = _lead_collected(lead)
    expenses = _lead_expenses(lead)
    margin = revenue - expenses
    margin_pct = (margin / revenue * 100) if revenue > 0 else None
    return {
        'lead': lead,
        'revenue': revenue,
        'collected': collected,
        'expenses': expenses,
        'margin': margin,
        'margin_pct': margin_pct,
    }


def build_project_costing_context(*, lead_id: int | None = None) -> dict:
    leads = list(
        SalesLead.objects.exclude(status=SalesLead.STATUS_CANCELLED)
        .select_related('customer')
        .prefetch_related('interim_payments')
        .order_by('-sale_date', '-created_at')
    )
    rows = [build_costing_row(lead) for lead in leads]
    rows.sort(key=lambda row: (-row['margin'], -row['revenue']))
    selected = None
    if lead_id:
        selected = next((row for row in rows if row['lead'].pk == lead_id), None)
    total_revenue = sum((row['revenue'] for row in rows), Decimal('0'))
    total_expenses = sum((row['expenses'] for row in rows), Decimal('0'))
    return {
        'costing_rows': rows,
        'costing_selected': selected,
        'costing_total_revenue': total_revenue,
        'costing_total_expenses': total_expenses,
        'costing_total_margin': total_revenue - total_expenses,
        'sales_leads_for_tag': leads[:100],
    }
