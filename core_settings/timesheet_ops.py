"""Zaman kaydı ve faturalama özeti."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from core_settings.models import ServicePersonnel, TimeEntry


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    from datetime import timedelta
    return start, end - timedelta(days=1)


def build_timesheet_context(*, year: int | None = None, month: int | None = None) -> dict:
    today = timezone.localdate()
    year = year or today.year
    month = month or today.month
    start, end = _month_bounds(year, month)

    entries = list(
        TimeEntry.objects.filter(entry_date__gte=start, entry_date__lte=end)
        .select_related('personnel', 'sales_lead', 'operational_project')
        .order_by('-entry_date', '-created_at')
    )
    total_hours = sum((entry.hours for entry in entries), Decimal('0'))
    billable_hours = sum(
        (entry.hours for entry in entries if entry.billable),
        Decimal('0'),
    )

    by_person: dict[int, dict] = {}
    for entry in entries:
        pid = entry.personnel_id or 0
        label = entry.personnel.name if entry.personnel else 'Atanmamış'
        bucket = by_person.setdefault(pid, {'label': label, 'hours': Decimal('0'), 'count': 0})
        bucket['hours'] += entry.hours
        bucket['count'] += 1
    person_totals = sorted(by_person.values(), key=lambda item: -item['hours'])

    personnel_choices = ServicePersonnel.objects.filter(is_active=True).order_by('name')

    return {
        'timesheet_entries': entries,
        'timesheet_total_hours': total_hours,
        'timesheet_billable_hours': billable_hours,
        'timesheet_person_totals': person_totals,
        'timesheet_year': year,
        'timesheet_month': month,
        'timesheet_personnel': personnel_choices,
    }


def create_time_entry(*, entry_date, hours: Decimal, description: str, personnel_id=None,
                      sales_lead_id=None, project_id=None, billable: bool, user) -> TimeEntry:
    if hours <= 0:
        raise ValueError('Saat 0\'dan büyük olmalı.')
    return TimeEntry.objects.create(
        entry_date=entry_date,
        hours=hours,
        description=description.strip(),
        billable=billable,
        personnel_id=personnel_id or None,
        sales_lead_id=sales_lead_id or None,
        operational_project_id=project_id or None,
        created_by=user,
    )
