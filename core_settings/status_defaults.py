"""Varsayılan servis durumları ve liste görünürlük mantığı."""

from __future__ import annotations

DEFAULT_STATUSES = [
    {'name': 'aktif', 'color': '#16a34a', 'sort_order': 10, 'list_group': 'active'},
    {'name': 'beklemede', 'color': '#d97706', 'sort_order': 20, 'list_group': 'pending'},
    {'name': 'tamamlandı', 'color': '#2563eb', 'sort_order': 30, 'list_group': 'hidden'},
    {'name': 'iptal', 'color': '#6b7280', 'sort_order': 40, 'list_group': 'hidden'},
    {'name': 'ücretli', 'color': '#ea580c', 'sort_order': 50, 'list_group': 'hidden'},
    {'name': 'iptal ücretli', 'color': '#dc2626', 'sort_order': 60, 'list_group': 'hidden'},
]


def ensure_default_statuses():
    from core_settings.models import StatusOption

    for item in DEFAULT_STATUSES:
        status, created = StatusOption.objects.get_or_create(
            name=item['name'],
            defaults={
                'color': item['color'],
                'sort_order': item['sort_order'],
                'list_group': item['list_group'],
            },
        )
        if not created:
            updates = {}
            if status.sort_order != item['sort_order']:
                updates['sort_order'] = item['sort_order']
            if status.list_group != item['list_group']:
                updates['list_group'] = item['list_group']
            if updates:
                StatusOption.objects.filter(pk=status.pk).update(**updates)


def apply_service_list_visibility(queryset, request):
    """Varsayılan: yalnızca aktif servisler; beklemede ve gizliler isteğe bağlı."""
    from core_settings.models import StatusOption

    explicit_status = (request.GET.get('status') or '').strip()
    if explicit_status and explicit_status.isdigit():
        return queryset.filter(status_id=int(explicit_status))

    show_hidden = request.GET.get('show_hidden') == '1'
    show_pending = request.GET.get('show_pending') == '1'
    groups = ['active']
    if show_pending:
        groups.append('pending')
    if show_hidden:
        groups.append('hidden')

    status_ids = list(
        StatusOption.objects.filter(list_group__in=groups).values_list('id', flat=True)
    )
    if not status_ids:
        ensure_default_statuses()
        status_ids = list(
            StatusOption.objects.filter(list_group__in=groups).values_list('id', flat=True)
        )
    return queryset.filter(status_id__in=status_ids)
