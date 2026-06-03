"""Müşteri 360° — satış, servis, alacak özeti."""

from __future__ import annotations

from decimal import Decimal

from django.utils import timezone

from customers.models import Customer
from sales_leads.models import SalesLead


def build_customer_overview(customer: Customer) -> dict:
    from sales_leads.collections import (
        annotate_sales_collection,
        collected_total_for_lead,
        remaining_balance_for_lead,
    )

    sales = list(
        annotate_sales_collection(
            SalesLead.objects.filter(customer=customer)
        )
        .prefetch_related('product_lines__product', 'interim_payments')
        .order_by('-sale_date', '-created_at')
    )
    receivable = sum(
        (
            remaining_balance_for_lead(lead)
            for lead in sales
            if remaining_balance_for_lead(lead) > 0
        ),
        Decimal('0'),
    )
    collected = sum((collected_total_for_lead(lead) for lead in sales), Decimal('0'))
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


def build_rehber_hub_stats(request=None) -> dict:
    """Rehber özeti için üst düzey KPI."""
    from services.models import ServiceRecord

    customers = Customer.objects.all()
    services = ServiceRecord.objects.all()
    if request is not None:
        from common.brand_scope import filter_customers, filter_services

        customers = filter_customers(customers, request)
        services = filter_services(services, request)

    customer_count = customers.count()
    receivable = Decimal('0')
    from sales_leads.collections import annotate_sales_collection, remaining_balance_for_lead

    leads = annotate_sales_collection(SalesLead.objects.all())
    if request is not None:
        from common.brand_scope import get_active_brand_id

        bid = get_active_brand_id(request)
        if bid:
            leads = leads.filter(customer__brand_id=bid)
    for lead in leads.iterator(chunk_size=500):
        remaining = remaining_balance_for_lead(lead)
        if remaining > 0:
            receivable += remaining

    return {
        'customer_count': customer_count,
        'open_service_count': services.count(),
        'total_receivable': receivable,
        'receivable_leads': SalesLead.objects.count(),
    }
