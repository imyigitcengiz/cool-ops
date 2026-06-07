"""Müşteri bazlı servis gruplama ve zaman çizelgesi."""

from __future__ import annotations

from collections import defaultdict

from django.urls import reverse

from core_settings.status_defaults import ensure_default_statuses

OPEN_LIST_GROUPS = frozenset({'active', 'pending'})


def _status_list_group(status) -> str:
    return getattr(status, 'list_group', None) or 'hidden'


def is_open_service(service) -> bool:
    return _status_list_group(service.status) in OPEN_LIST_GROUPS


def get_active_status():
    ensure_default_statuses()
    from core_settings.models import StatusOption

    return (
        StatusOption.objects.filter(list_group='active')
        .order_by('sort_order', 'name')
        .first()
    )


def serialize_service_brief(service, *, include_edit_url=True):
    types = ', '.join(st.name for st in service.service_types.all()[:4]) or '-'
    notes = (service.notes or '').strip()
    if len(notes) > 120:
        notes = notes[:117] + '…'
    payload = {
        'id': service.id,
        'status_id': service.status_id,
        'status_name': service.status.name,
        'status_color': service.status.color_hex,
        'list_group': _status_list_group(service.status),
        'is_open': is_open_service(service),
        'priority_name': service.priority.name if service.priority_id else '',
        'created_at': service.created_at.strftime('%d.%m.%Y %H:%M') if service.created_at else '',
        'created_date': service.created_at.strftime('%d.%m.%Y') if service.created_at else '',
        'service_types': types,
        'notes_preview': notes or '-',
    }
    if include_edit_url:
        payload['edit_url'] = reverse('service_update', args=[service.pk])
        payload['print_url'] = reverse('service_print', args=[service.pk])
    return payload


def customer_services_payload(customer_id, *, timeline_limit=40, request=None):
    from .models import ServiceRecord

    ensure_default_statuses()
    qs = ServiceRecord.objects.filter(customer_id=customer_id)
    if request is not None:
        from common.brand_scope import filter_services

        qs = filter_services(qs, request)
    qs = (
        qs.select_related('status', 'priority', 'customer')
        .prefetch_related('service_types', 'products')
        .order_by('-created_at')
    )
    records = list(qs[:timeline_limit])
    open_services = [serialize_service_brief(s) for s in records if is_open_service(s)]
    timeline = [serialize_service_brief(s) for s in records]
    return {
        'ok': True,
        'open_services': open_services,
        'timeline': timeline,
        'counts': {
            'total': qs.count(),
            'open': qs.filter(status__list_group__in=OPEN_LIST_GROUPS).count(),
            'shown': len(records),
        },
    }


def build_service_customer_groups(queryset):
    """Filtrelenmiş queryset'i müşteri başına grupla; öne açık/en güncel kaydı çıkar."""
    by_customer = defaultdict(list)
    for service in queryset:
        by_customer[service.customer_id].append(service)

    groups = []
    for records in by_customer.values():
        records.sort(
            key=lambda s: (
                0 if is_open_service(s) else 1,
                -(s.created_at.timestamp() if s.created_at else 0),
            )
        )
        primary = records[0]
        open_count = sum(1 for r in records if is_open_service(r))
        groups.append({
            'primary': primary,
            'records': records,
            'other_count': max(len(records) - 1, 0),
            'open_count': open_count,
            'has_multiple_open': open_count > 1,
        })

    groups.sort(
        key=lambda g: (
            -g['open_count'],
            -(g['primary'].created_at.timestamp() if g['primary'].created_at else 0),
        )
    )
    return groups
