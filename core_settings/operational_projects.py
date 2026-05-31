"""Operasyon projeleri — müşteri / satış bağlantılı proje kartları."""

from __future__ import annotations

from core_settings.models import OperationalProject


def build_projects_context() -> dict:
    projects = list(
        OperationalProject.objects.select_related('customer', 'sales_lead')
        .order_by('-created_at')
    )
    by_status: dict[str, list] = {code: [] for code, _ in OperationalProject.STATUS_CHOICES}
    for project in projects:
        by_status.setdefault(project.status, []).append(project)
    return {
        'operational_projects': projects,
        'projects_by_status': by_status,
        'project_status_choices': OperationalProject.STATUS_CHOICES,
    }


def create_project(*, name: str, customer_id=None, sales_lead_id=None, status: str, notes: str = '') -> OperationalProject:
    return OperationalProject.objects.create(
        name=name.strip(),
        customer_id=customer_id or None,
        sales_lead_id=sales_lead_id or None,
        status=status or OperationalProject.STATUS_ACTIVE,
        notes=notes.strip(),
    )
