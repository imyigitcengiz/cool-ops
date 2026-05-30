"""Ajans proje — deliverable, maliyet ve pipeline yardımcıları."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from agency.models import (
    AgencyDeal,
    AgencyDeliverable,
    AgencyFinanceEntry,
    AgencyProject,
    AgencyProjectAssignment,
)


def project_queryset_for_user(user):
    qs = AgencyProject.objects.select_related('client', 'owner', 'source_deal')
    if not user.is_superuser:
        qs = qs.filter(Q(owner=user) | Q(owner__isnull=True))
    return qs


def deliverable_progress(project: AgencyProject) -> dict:
    qs = project.deliverables.all()
    total = qs.count()
    done = qs.filter(is_done=True).count()
    pct = int((done / total) * 100) if total else 0
    overdue = qs.filter(is_done=False, due_date__lt=timezone.localdate()).count()
    return {'total': total, 'done': done, 'percent': pct, 'overdue': overdue}


def freelancer_cost_estimate(project: AgencyProject) -> Decimal:
    total = Decimal('0')
    for row in project.assignments.select_related('freelancer'):
        rate = row.hourly_rate_override or row.freelancer.hourly_rate
        if rate and row.hours_budget:
            total += rate * row.hours_budget
    return total


def project_margin(project: AgencyProject) -> dict | None:
    retainer = project.monthly_retainer
    if retainer is None:
        return None
    cost = freelancer_cost_estimate(project)
    margin = retainer - cost
    pct = int((margin / retainer) * 100) if retainer else 0
    return {
        'retainer': retainer,
        'freelancer_cost': cost,
        'margin': margin,
        'margin_percent': pct,
    }


def weighted_pipeline_value() -> Decimal:
    weights = {
        AgencyDeal.Stage.LEAD: Decimal('0.15'),
        AgencyDeal.Stage.PROPOSAL: Decimal('0.45'),
        AgencyDeal.Stage.WON: Decimal('1'),
        AgencyDeal.Stage.LOST: Decimal('0'),
    }
    total = Decimal('0')
    for deal in AgencyDeal.objects.exclude(stage=AgencyDeal.Stage.LOST).exclude(amount__isnull=True):
        total += (deal.amount or 0) * weights.get(deal.stage, Decimal('0.25'))
    return total


def convert_deal_to_project(deal: AgencyDeal, *, owner) -> AgencyProject:
    if deal.converted_project_id:
        return deal.converted_project
    name = deal.title
    if deal.client:
        name = f'{deal.client.name} — {deal.title}'
    project = AgencyProject.objects.create(
        name=name[:200],
        client=deal.client,
        status=AgencyProject.Status.ACTIVE if deal.stage == AgencyDeal.Stage.WON else AgencyProject.Status.LEAD,
        monthly_retainer=deal.amount,
        owner=owner,
        source_deal=deal,
        scope_summary=deal.notes or '',
    )
    deal.converted_project = project
    deal.stage = AgencyDeal.Stage.WON
    deal.save(update_fields=['converted_project', 'stage', 'updated_at'])
    return project


def pipeline_by_stage() -> dict[str, list]:
    columns = {s.value: [] for s in AgencyDeal.Stage}
    for deal in AgencyDeal.objects.select_related('client', 'converted_project').order_by('-updated_at'):
        columns.setdefault(deal.stage, []).append(deal)
    return columns
