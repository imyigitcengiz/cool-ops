"""Müşteri 360° — satış, servis, alacak özeti."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from customers.models import Customer
from sales_leads.models import SalesLead


def build_customer_overview(customer: Customer) -> dict:
    sales = list(
        SalesLead.objects.filter(customer=customer)
        .prefetch_related('product_lines__product', 'interim_payments')
        .order_by('-sale_date', '-created_at')
    )
    receivable = sum(
        (lead.remaining_balance for lead in sales if lead.remaining_balance > 0),
        Decimal('0'),
    )
    collected = sum(
        (lead.down_payment or Decimal('0')) + lead.interim_payments_total for lead in sales
    )
    sale_total = sum((lead.sale_amount or Decimal('0')) for lead in sales)

    services = customer.service_records.select_related('status', 'service_personnel').order_by('-created_at')
    service_count = services.count()
    last_service = services.first()

    return {
        'sales': sales,
        'sales_count': len(sales),
        'sale_total': sale_total,
        'collected_total': collected,
        'receivable_total': receivable,
        'services': services[:20],
        'service_count': service_count,
        'last_service': last_service,
        'today': timezone.localdate(),
    }


def build_rehber_hub_stats() -> dict:
    """Rehber özeti için üst düzey KPI."""
    from services.models import ServiceRecord

    customer_count = Customer.objects.count()
    receivable = Decimal('0')
    leads = SalesLead.objects.annotate(
        _interim_total=Coalesce(
            Sum('interim_payments__amount'),
            Value(Decimal('0')),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    )
    for lead in leads.iterator(chunk_size=500):
        total = lead.sale_amount or Decimal('0')
        paid = (lead.down_payment or Decimal('0')) + lead._interim_total
        remaining = total - paid
        if remaining > 0:
            receivable += remaining

    return {
        'customer_count': customer_count,
        'open_service_count': ServiceRecord.objects.count(),
        'total_receivable': receivable,
        'receivable_leads': SalesLead.objects.count(),
    }
