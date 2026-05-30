from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView

from agency.models import (
    AgencyCampaign,
    AgencyClient,
    AgencyDeal,
    AgencyDeliverable,
    AgencyFinanceEntry,
    AgencyFirm,
    AgencyFreelancer,
    AgencyProject,
    AgencyProjectAssignment,
)
from agency.project_services import (
    convert_deal_to_project,
    deliverable_progress,
    pipeline_by_stage,
    project_margin,
    project_queryset_for_user,
    weighted_pipeline_value,
)
from agency.summary import build_agency_panel_context
from users.mixins import PermissionRequiredMixin


class AgencyAccessMixin(PermissionRequiredMixin):
    permission_required = 'access.agency'


def _decimal(raw, default=None):
    if raw in (None, ''):
        return default
    try:
        return Decimal(str(raw).replace(',', '.'))
    except (InvalidOperation, ValueError):
        return default


def _int_clamp(raw, default=0, lo=0, hi=100):
    try:
        v = int(raw)
        return max(lo, min(hi, v))
    except (TypeError, ValueError):
        return default


class AgencyHubView(AgencyAccessMixin, TemplateView):
    template_name = 'agency/hub.html'
    agency_nav_active = 'hub'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_agency_panel_context(self.request.user))
        context['agency_nav_active'] = self.agency_nav_active
        qs = project_queryset_for_user(self.request.user).prefetch_related('deliverables')
        context['agency_projects'] = qs[:50]
        context['agency_clients'] = AgencyClient.objects.order_by('name')[:200]
        context['agency_status_choices'] = AgencyProject.Status.choices
        context['pipeline_stages_preview'] = pipeline_by_stage()
        return context

    def post(self, request, *args, **kwargs):
        name = (request.POST.get('name') or '').strip()
        if not name:
            messages.error(request, 'Proje adı gerekli.')
            return redirect('agency_hub')
        client = AgencyClient.objects.filter(pk=request.POST.get('client_id')).first()
        project = AgencyProject.objects.create(
            name=name,
            status=request.POST.get('status', AgencyProject.Status.LEAD),
            monthly_retainer=_decimal(request.POST.get('monthly_retainer')),
            client=client,
            scope_summary=request.POST.get('scope_summary', ''),
            owner=request.user,
        )
        messages.success(request, f'"{name}" oluşturuldu.')
        return redirect('agency_project_detail', pk=project.pk)


class AgencyProjectDetailView(AgencyAccessMixin, TemplateView):
    template_name = 'agency/project_detail.html'
    agency_nav_active = 'hub'

    def get_project(self):
        return get_object_or_404(
            project_queryset_for_user(self.request.user).prefetch_related(
                'deliverables', 'assignments__freelancer', 'finance_entries',
            ),
            pk=self.kwargs['pk'],
        )

    def get_context_data(self, **kwargs):
        project = self.get_project()
        context = super().get_context_data(**kwargs)
        context['agency_nav_active'] = self.agency_nav_active
        context['project'] = project
        context['progress'] = deliverable_progress(project)
        context['margin'] = project_margin(project)
        context['clients'] = AgencyClient.objects.order_by('name')
        context['freelancers'] = AgencyFreelancer.objects.filter(is_active=True).order_by('name')
        context['status_choices'] = AgencyProject.Status.choices
        context['finance_entries'] = project.finance_entries.order_by('-entry_date')[:10]
        return context

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        action = request.POST.get('action', 'update_project')

        if action == 'delete_project':
            name = project.name
            project.delete()
            messages.success(request, f'"{name}" silindi.')
            return redirect('agency_hub')

        if action == 'add_deliverable':
            title = (request.POST.get('title') or '').strip()
            if title:
                AgencyDeliverable.objects.create(
                    project=project,
                    title=title,
                    due_date=parse_date(request.POST.get('due_date') or ''),
                    sort_order=project.deliverables.count(),
                )
                messages.success(request, 'Deliverable eklendi.')
            return redirect('agency_project_detail', pk=project.pk)

        if action == 'toggle_deliverable':
            d = get_object_or_404(AgencyDeliverable, pk=request.POST.get('deliverable_id'), project=project)
            d.is_done = not d.is_done
            d.completed_at = timezone.now() if d.is_done else None
            d.save(update_fields=['is_done', 'completed_at'])
            return redirect('agency_project_detail', pk=project.pk)

        if action == 'delete_deliverable':
            AgencyDeliverable.objects.filter(pk=request.POST.get('deliverable_id'), project=project).delete()
            return redirect('agency_project_detail', pk=project.pk)

        if action == 'add_assignment':
            fl = AgencyFreelancer.objects.filter(pk=request.POST.get('freelancer_id')).first()
            if fl:
                AgencyProjectAssignment.objects.get_or_create(
                    project=project,
                    freelancer=fl,
                    defaults={
                        'role_label': request.POST.get('role_label', ''),
                        'hours_budget': _decimal(request.POST.get('hours_budget')),
                        'hourly_rate_override': _decimal(request.POST.get('hourly_rate_override')),
                    },
                )
                messages.success(request, f'{fl.name} atandı.')
            return redirect('agency_project_detail', pk=project.pk)

        if action == 'delete_assignment':
            AgencyProjectAssignment.objects.filter(
                pk=request.POST.get('assignment_id'), project=project,
            ).delete()
            return redirect('agency_project_detail', pk=project.pk)

        project.name = (request.POST.get('name') or project.name).strip()
        project.status = request.POST.get('status', project.status)
        project.monthly_retainer = _decimal(request.POST.get('monthly_retainer'), project.monthly_retainer)
        project.scope_summary = request.POST.get('scope_summary', '')
        project.revision_rounds_included = _int_clamp(
            request.POST.get('revision_rounds_included'), project.revision_rounds_included, 0, 20,
        )
        project.monthly_hours_cap = _decimal(request.POST.get('monthly_hours_cap'))
        project.client = AgencyClient.objects.filter(pk=request.POST.get('client_id')).first()
        project.start_date = parse_date(request.POST.get('start_date') or '') or project.start_date
        project.end_date = parse_date(request.POST.get('end_date') or '') or project.end_date
        project.notes = request.POST.get('notes', '')
        project.save()
        messages.success(request, 'Proje güncellendi.')
        return redirect('agency_project_detail', pk=project.pk)


class AgencyClientDetailView(AgencyAccessMixin, TemplateView):
    template_name = 'agency/client_detail.html'
    agency_nav_active = 'clients'

    def get_context_data(self, **kwargs):
        client = get_object_or_404(AgencyClient, pk=self.kwargs['pk'])
        context = super().get_context_data(**kwargs)
        context['agency_nav_active'] = self.agency_nav_active
        context['client'] = client
        context['projects'] = client.projects.select_related('owner').all()
        context['deals'] = client.deals.all()
        context['campaigns'] = client.campaigns.all()
        retainer = client.projects.filter(status=AgencyProject.Status.ACTIVE).aggregate(
            s=Sum('monthly_retainer'),
        )['s'] or Decimal('0')
        context['client_mrr'] = retainer
        return context


class AgencyClientsView(AgencyAccessMixin, TemplateView):
    template_name = 'agency/clients.html'
    agency_nav_active = 'clients'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency_nav_active'] = self.agency_nav_active
        context['items'] = AgencyClient.objects.annotate(
            project_count=Count('projects'),
        ).order_by('name')
        context['contract_choices'] = AgencyClient._meta.get_field('contract_type').choices
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'delete':
            get_object_or_404(AgencyClient, pk=request.POST.get('pk')).delete()
            messages.success(request, 'Müşteri silindi.')
            return redirect('agency_clients')

        pk = request.POST.get('pk')
        name = (request.POST.get('name') or '').strip()
        if not name:
            messages.error(request, 'Ad gerekli.')
            return redirect('agency_clients')

        data = {
            'name': name,
            'contact_name': request.POST.get('contact_name', ''),
            'email': request.POST.get('email', ''),
            'phone': request.POST.get('phone', ''),
            'contract_type': request.POST.get('contract_type', 'retainer'),
            'industry': request.POST.get('industry', ''),
            'website': request.POST.get('website', ''),
            'contract_start': parse_date(request.POST.get('contract_start') or ''),
            'contract_end': parse_date(request.POST.get('contract_end') or ''),
            'notes': request.POST.get('notes', ''),
        }
        if pk:
            AgencyClient.objects.filter(pk=pk).update(**data)
            messages.success(request, 'Müşteri güncellendi.')
            return redirect('agency_client_detail', pk=pk)
        client = AgencyClient.objects.create(**data)
        messages.success(request, 'Müşteri eklendi.')
        return redirect('agency_client_detail', pk=client.pk)


class AgencyFreelancersView(AgencyAccessMixin, TemplateView):
    template_name = 'agency/freelancers.html'
    agency_nav_active = 'freelancers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency_nav_active'] = self.agency_nav_active
        context['items'] = AgencyFreelancer.objects.annotate(
            assignment_count=Count('assignments'),
        ).order_by('name')
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'delete':
            get_object_or_404(AgencyFreelancer, pk=request.POST.get('pk')).delete()
            messages.success(request, 'Freelancer silindi.')
            return redirect('agency_freelancers')

        pk = request.POST.get('pk')
        name = (request.POST.get('name') or '').strip()
        if not name:
            messages.error(request, 'Ad gerekli.')
            return redirect('agency_freelancers')

        data = {
            'name': name,
            'specialty': request.POST.get('specialty', ''),
            'hourly_rate': _decimal(request.POST.get('hourly_rate')),
            'email': request.POST.get('email', ''),
            'phone': request.POST.get('phone', ''),
            'is_active': request.POST.get('is_active') == 'on',
            'notes': request.POST.get('notes', ''),
        }
        if pk:
            AgencyFreelancer.objects.filter(pk=pk).update(**data)
            messages.success(request, 'Freelancer güncellendi.')
        else:
            AgencyFreelancer.objects.create(**data)
            messages.success(request, 'Freelancer eklendi.')
        return redirect('agency_freelancers')


class AgencyFirmsView(AgencyAccessMixin, TemplateView):
    template_name = 'agency/firms.html'
    agency_nav_active = 'firms'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency_nav_active'] = self.agency_nav_active
        context['items'] = AgencyFirm.objects.all()
        context['status_choices'] = AgencyFirm.Status.choices
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'delete':
            get_object_or_404(AgencyFirm, pk=request.POST.get('pk')).delete()
            messages.success(request, 'Firma silindi.')
            return redirect('agency_firms')

        pk = request.POST.get('pk')
        name = (request.POST.get('name') or '').strip()
        if not name:
            messages.error(request, 'Firma adı gerekli.')
            return redirect('agency_firms')

        data = {
            'name': name,
            'city': request.POST.get('city', ''),
            'website': request.POST.get('website', ''),
            'status': request.POST.get('status', AgencyFirm.Status.PROSPECT),
            'notes': request.POST.get('notes', ''),
        }
        if pk:
            AgencyFirm.objects.filter(pk=pk).update(**data)
            messages.success(request, 'Firma güncellendi.')
        else:
            AgencyFirm.objects.create(**data)
            messages.success(request, 'Firma eklendi.')
        return redirect('agency_firms')


class AgencyPipelineView(AgencyAccessMixin, TemplateView):
    template_name = 'agency/pipeline.html'
    agency_nav_active = 'pipeline'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency_nav_active'] = self.agency_nav_active
        columns = pipeline_by_stage()
        stage_meta = [
            (AgencyDeal.Stage.LEAD, 'Lead', 'amber'),
            (AgencyDeal.Stage.PROPOSAL, 'Teklif', 'sky'),
            (AgencyDeal.Stage.WON, 'Kazanıldı', 'emerald'),
            (AgencyDeal.Stage.LOST, 'Kayıp', 'slate'),
        ]
        context['pipeline_board'] = [
            {
                'stage': stage,
                'label': label,
                'color': color,
                'deals': columns.get(stage, []),
            }
            for stage, label, color in stage_meta
        ]
        context['clients'] = AgencyClient.objects.order_by('name')
        context['pipeline_weighted'] = weighted_pipeline_value()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', 'create_deal')

        if action == 'convert_to_project':
            deal = get_object_or_404(AgencyDeal, pk=request.POST.get('deal_id'))
            project = convert_deal_to_project(deal, owner=request.user)
            messages.success(request, f'"{deal.title}" → retainer projesi oluşturuldu.')
            return redirect('agency_project_detail', pk=project.pk)

        if action == 'move_stage':
            deal = get_object_or_404(AgencyDeal, pk=request.POST.get('deal_id'))
            stage = request.POST.get('stage')
            if stage in dict(AgencyDeal.Stage.choices):
                deal.stage = stage
                deal.save(update_fields=['stage', 'updated_at'])
            return redirect('agency_pipeline')

        if action == 'delete':
            get_object_or_404(AgencyDeal, pk=request.POST.get('pk')).delete()
            messages.success(request, 'Silindi.')
            return redirect('agency_pipeline')

        title = (request.POST.get('title') or '').strip()
        if not title:
            messages.error(request, 'Başlık gerekli.')
            return redirect('agency_pipeline')

        pk = request.POST.get('pk')
        client = AgencyClient.objects.filter(pk=request.POST.get('client_id')).first()
        data = {
            'title': title,
            'client': client,
            'amount': _decimal(request.POST.get('amount')),
            'stage': request.POST.get('stage', AgencyDeal.Stage.LEAD),
            'probability': _int_clamp(request.POST.get('probability'), 30),
            'expected_close': parse_date(request.POST.get('expected_close') or ''),
            'notes': request.POST.get('notes', ''),
        }
        if pk:
            AgencyDeal.objects.filter(pk=pk).update(**data)
            messages.success(request, 'Güncellendi.')
        else:
            AgencyDeal.objects.create(owner=request.user, **data)
            messages.success(request, 'Fırsat eklendi.')
        return redirect('agency_pipeline')


class AgencyFinanceView(AgencyAccessMixin, TemplateView):
    template_name = 'agency/finance.html'
    agency_nav_active = 'finance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency_nav_active'] = self.agency_nav_active
        context['items'] = AgencyFinanceEntry.objects.select_related('project', 'project__client').all()[:200]
        context['projects'] = AgencyProject.objects.select_related('client').order_by('name')
        context['kind_choices'] = AgencyFinanceEntry.Kind.choices
        entries = AgencyFinanceEntry.objects.all()
        income = entries.filter(kind=AgencyFinanceEntry.Kind.INCOME).aggregate(s=Sum('amount'))['s'] or 0
        expense = entries.filter(kind=AgencyFinanceEntry.Kind.EXPENSE).aggregate(s=Sum('amount'))['s'] or 0
        context['finance_income'] = income
        context['finance_expense'] = expense
        context['finance_net'] = income - expense
        active_retainer = AgencyProject.objects.filter(
            status=AgencyProject.Status.ACTIVE,
        ).aggregate(s=Sum('monthly_retainer'))['s'] or Decimal('0')
        context['finance_mrr'] = active_retainer
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'delete':
            get_object_or_404(AgencyFinanceEntry, pk=request.POST.get('pk')).delete()
            messages.success(request, 'Kayıt silindi.')
            return redirect('agency_finance')

        pk = request.POST.get('pk')
        title = (request.POST.get('title') or '').strip()
        amount = _decimal(request.POST.get('amount'))
        entry_date = parse_date(request.POST.get('entry_date') or '') or timezone.localdate()
        if not title or amount is None:
            messages.error(request, 'Başlık ve tutar gerekli.')
            return redirect('agency_finance')

        project = AgencyProject.objects.filter(pk=request.POST.get('project_id')).first()
        data = {
            'title': title,
            'kind': request.POST.get('kind', AgencyFinanceEntry.Kind.INCOME),
            'amount': amount,
            'entry_date': entry_date,
            'project': project,
            'notes': request.POST.get('notes', ''),
        }
        if pk:
            AgencyFinanceEntry.objects.filter(pk=pk).update(**data)
            messages.success(request, 'Finans kaydı güncellendi.')
        else:
            AgencyFinanceEntry.objects.create(**data)
            messages.success(request, 'Finans kaydı eklendi.')
        return redirect('agency_finance')


class AgencyCampaignsView(AgencyAccessMixin, TemplateView):
    template_name = 'agency/campaigns.html'
    agency_nav_active = 'campaigns'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency_nav_active'] = self.agency_nav_active
        context['items'] = AgencyCampaign.objects.select_related('target_client').all()
        context['clients'] = AgencyClient.objects.order_by('name')
        context['status_choices'] = AgencyCampaign.Status.choices
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'delete':
            get_object_or_404(AgencyCampaign, pk=request.POST.get('pk')).delete()
            messages.success(request, 'Kampanya silindi.')
            return redirect('agency_campaigns')

        pk = request.POST.get('pk')
        name = (request.POST.get('name') or '').strip()
        if not name:
            messages.error(request, 'Kampanya adı gerekli.')
            return redirect('agency_campaigns')

        client = AgencyClient.objects.filter(pk=request.POST.get('target_client_id')).first()
        data = {
            'name': name,
            'message_body': request.POST.get('message_body', ''),
            'status': request.POST.get('status', AgencyCampaign.Status.DRAFT),
            'target_client': client,
        }
        if pk:
            AgencyCampaign.objects.filter(pk=pk).update(**data)
            messages.success(request, 'Kampanya güncellendi.')
        else:
            AgencyCampaign.objects.create(**data)
            messages.success(request, 'Kampanya eklendi.')
        return redirect('agency_campaigns')
