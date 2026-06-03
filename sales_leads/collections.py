"""Satış tahsilatı — peşinat, ara ödeme ve satışa bağlı gelir kayıtları."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from core_settings.models import FinanceRecord


def finance_income_for_lead(lead) -> Decimal:
    if hasattr(lead, '_finance_income_total'):
        return lead._finance_income_total or Decimal('0')
    total = (
        lead.finance_records.filter(record_type=FinanceRecord.TYPE_INCOME)
        .aggregate(t=Sum('amount'))['t']
    )
    return total or Decimal('0')


def interim_total_for_lead(lead) -> Decimal:
    if hasattr(lead, '_interim_total'):
        return lead._interim_total or Decimal('0')
    return sum((p.amount or Decimal('0')) for p in lead.interim_payments.all())


def collected_total_for_lead(lead) -> Decimal:
    """Tahsil edilen: peşinat + ara ödemeler + satışa bağlı gelir kayıtları."""
    return (
        (lead.down_payment or Decimal('0'))
        + interim_total_for_lead(lead)
        + finance_income_for_lead(lead)
    )


def remaining_balance_for_lead(lead) -> Decimal:
    total = lead.sale_amount or Decimal('0')
    return total - collected_total_for_lead(lead)


def annotate_sales_collection(qs):
    """Liste sorguları için tahsilat toplamları."""
    return qs.annotate(
        _interim_total=Coalesce(
            Sum('interim_payments__amount'),
            Value(Decimal('0')),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
        _finance_income_total=Coalesce(
            Sum(
                'finance_records__amount',
                filter=Q(finance_records__record_type=FinanceRecord.TYPE_INCOME),
            ),
            Value(Decimal('0')),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    )
