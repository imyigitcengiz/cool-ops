"""Ajans panel KPI özeti."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from agency.models import AgencyDeal, AgencyDeliverable, AgencyFinanceEntry, AgencyProject
from agency.project_services import project_queryset_for_user, weighted_pipeline_value


def build_agency_panel_context(user) -> dict:
    qs = project_queryset_for_user(user)

    active = qs.filter(status=AgencyProject.Status.ACTIVE)
    retainer_sum = active.aggregate(total=Sum('monthly_retainer'))['total'] or Decimal('0')

    by_status = dict(
        qs.values('status').annotate(c=Count('id')).values_list('status', 'c')
    )

    pipeline_open = AgencyDeal.objects.exclude(
        stage__in=(AgencyDeal.Stage.WON, AgencyDeal.Stage.LOST)
    ).count()

    deliverable_stats = AgencyDeliverable.objects.filter(
        project__in=qs.filter(status=AgencyProject.Status.ACTIVE),
        is_done=False,
    ).aggregate(
        open=Count('id'),
        overdue=Count('id', filter=Q(due_date__lt=timezone.localdate())),
    )

    month_start = timezone.localdate().replace(day=1)
    finance_month = AgencyFinanceEntry.objects.filter(entry_date__gte=month_start).aggregate(
        income=Sum('amount', filter=Q(kind=AgencyFinanceEntry.Kind.INCOME)),
        expense=Sum('amount', filter=Q(kind=AgencyFinanceEntry.Kind.EXPENSE)),
    )

    return {
        'agency_project_count': qs.count(),
        'agency_active_count': by_status.get(AgencyProject.Status.ACTIVE, 0),
        'agency_lead_count': by_status.get(AgencyProject.Status.LEAD, 0),
        'agency_retainer_monthly': retainer_sum,
        'agency_arr': retainer_sum * 12 if retainer_sum else Decimal('0'),
        'agency_recent_projects': list(
            qs.select_related('client', 'owner').prefetch_related('deliverables')[:6]
        ),
        'agency_pipeline_open': pipeline_open,
        'agency_pipeline_weighted': weighted_pipeline_value(),
        'agency_deliverables_open': deliverable_stats.get('open') or 0,
        'agency_deliverables_overdue': deliverable_stats.get('overdue') or 0,
        'agency_finance_month_income': finance_month.get('income') or Decimal('0'),
        'agency_finance_month_expense': finance_month.get('expense') or Decimal('0'),
    }
