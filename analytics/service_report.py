from __future__ import annotations

from calendar import monthrange
from datetime import date

from django.db.models import Count, Q
from django.utils import timezone

from core_settings.models import StatusOption
from core_settings.status_defaults import ensure_default_statuses
from services.models import ServiceRecord

TR_MONTHS = ('Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara')

CANCELLED_Q = Q(status__name__icontains='iptal')
ACTIVE_Q = Q(status__list_group=StatusOption.LIST_ACTIVE)
PENDING_Q = Q(status__list_group=StatusOption.LIST_PENDING)
CLOSED_Q = Q(status__list_group=StatusOption.LIST_HIDDEN) & ~CANCELLED_Q


def _month_label(year: int, month: int, today: date) -> str:
    name = TR_MONTHS[month - 1]
    if year == today.year:
        return name
    return f'{name} {str(year)[-2:]}'


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end = date(year, month, last_day)
    return start, end


def _last_n_months(n: int = 12, today: date | None = None) -> list[tuple[int, int]]:
    today = today or timezone.localdate()
    anchor = today.year * 12 + (today.month - 1)
    return [
        ((anchor - offset) // 12, (anchor - offset) % 12 + 1)
        for offset in range(n - 1, -1, -1)
    ]


def _pct(part: int, whole: int) -> float:
    if not whole:
        return 0.0
    return round(part / whole * 100, 1)


def build_service_dashboard_report(request=None):
    ensure_default_statuses()
    today = timezone.localdate()
    month_start, _ = _month_bounds(today.year, today.month)

    all_services = ServiceRecord.objects.select_related('status', 'priority', 'customer')
    if request is not None:
        from common.brand_scope import filter_services

        all_services = filter_services(all_services, request)
    total_services = all_services.count()

    active_count = all_services.filter(ACTIVE_Q).count()
    pending_count = all_services.filter(PENDING_Q).count()
    closed_count = all_services.filter(CLOSED_Q).count()
    cancelled_count = all_services.filter(CANCELLED_Q).count()

    month_new = all_services.filter(created_at__date__gte=month_start).count()
    prev_month_year, prev_month = _last_n_months(2, today)[0]
    prev_start, prev_end = _month_bounds(prev_month_year, prev_month)
    prev_month_new = all_services.filter(
        created_at__date__gte=prev_start,
        created_at__date__lte=prev_end,
    ).count()
    month_delta = month_new - prev_month_new

    monthly_rows = []
    monthly_active = []
    monthly_pending = []
    monthly_closed = []
    monthly_cancelled = []
    monthly_total = []
    monthly_labels = []

    for year, month in _last_n_months(12, today):
        start, end = _month_bounds(year, month)
        month_qs = all_services.filter(
            created_at__date__gte=start,
            created_at__date__lte=end,
        )
        row_active = month_qs.filter(ACTIVE_Q).count()
        row_pending = month_qs.filter(PENDING_Q).count()
        row_closed = month_qs.filter(CLOSED_Q).count()
        row_cancelled = month_qs.filter(CANCELLED_Q).count()
        row_total = month_qs.count()

        monthly_labels.append(_month_label(year, month, today))
        monthly_active.append(row_active)
        monthly_pending.append(row_pending)
        monthly_closed.append(row_closed)
        monthly_cancelled.append(row_cancelled)
        monthly_total.append(row_total)
        monthly_rows.append({
            'label': _month_label(year, month, today),
            'year': year,
            'month': month,
            'total': row_total,
            'active': row_active,
            'pending': row_pending,
            'closed': row_closed,
            'cancelled': row_cancelled,
        })

    monthly_rows.sort(key=lambda row: (row['year'], row['month']), reverse=True)

    status_rows = (
        all_services.values('status__name', 'status__color', 'status__list_group', 'status__sort_order')
        .annotate(total=Count('id'))
        .order_by('status__sort_order', 'status__name')
    )
    status_breakdown = []
    for row in status_rows:
        name = row['status__name'] or 'Durum yok'
        lower = name.lower()
        if 'iptal' in lower:
            bucket = 'cancelled'
            bucket_label = 'İptal'
        elif row['status__list_group'] == StatusOption.LIST_ACTIVE:
            bucket = 'active'
            bucket_label = 'Aktif'
        elif row['status__list_group'] == StatusOption.LIST_PENDING:
            bucket = 'pending'
            bucket_label = 'Beklemede'
        else:
            bucket = 'closed'
            bucket_label = 'Kapalı'
        status_breakdown.append({
            'name': name,
            'color': row['status__color'] or '#64748b',
            'total': row['total'],
            'pct': _pct(row['total'], total_services),
            'bucket': bucket,
            'bucket_label': bucket_label,
        })

    product_stats = (
        all_services.filter(products__isnull=False)
        .values('products__name', 'products__color')
        .annotate(total=Count('id', distinct=True))
        .order_by('-total')[:8]
    )
    product_labels = [p['products__name'] or '—' for p in product_stats]
    product_counts = [p['total'] for p in product_stats]
    product_colors = [p['products__color'] or '#0284c7' for p in product_stats]

    priority_stats = (
        all_services.values('priority__name', 'priority__color')
        .annotate(total=Count('id'))
        .order_by('-total')[:6]
    )
    priority_breakdown = [
        {
            'name': p['priority__name'] or '—',
            'color': p['priority__color'] or '#64748b',
            'total': p['total'],
            'pct': _pct(p['total'], total_services),
        }
        for p in priority_stats
    ]

    open_services = all_services.filter(ACTIVE_Q | PENDING_Q).count()
    completion_rate = _pct(closed_count, total_services)
    cancellation_rate = _pct(cancelled_count, total_services)

    return {
        'report_generated_at': timezone.localtime(),
        'total_services': total_services,
        'service_counts': {
            'active': active_count,
            'pending': pending_count,
            'closed': closed_count,
            'cancelled': cancelled_count,
            'open': open_services,
            'active_pct': _pct(active_count, total_services),
            'pending_pct': _pct(pending_count, total_services),
            'closed_pct': _pct(closed_count, total_services),
            'cancelled_pct': _pct(cancelled_count, total_services),
        },
        'month_new': month_new,
        'month_delta': month_delta,
        'prev_month_new': prev_month_new,
        'completion_rate': completion_rate,
        'cancellation_rate': cancellation_rate,
        'warranty_active_count': all_services.filter(warranty_status='active').count(),
        'monthly_labels': monthly_labels,
        'monthly_active': monthly_active,
        'monthly_pending': monthly_pending,
        'monthly_closed': monthly_closed,
        'monthly_cancelled': monthly_cancelled,
        'monthly_total': monthly_total,
        'monthly_rows': monthly_rows,
        'status_breakdown': status_breakdown,
        'product_labels': product_labels,
        'product_counts': product_counts,
        'product_colors': product_colors,
        'priority_breakdown': priority_breakdown,
        'recent_services': (
            all_services.prefetch_related('products')
            .order_by('-created_at')[:8]
        ),
    }
