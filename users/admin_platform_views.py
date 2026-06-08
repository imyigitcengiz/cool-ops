import csv
import io

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, TemplateView

from core_settings.models import BillingInvoice, Plan, SiteSettings

from .admin_forms import AdminBillingInvoiceForm, AdminPlanForm, AdminSiteSettingsForm
from .admin_services import membership_matrix_rows, usage_report_csv_rows
from .mixins import SuperuserRequiredMixin
from .models import ImpersonationAudit, PlatformAuditLog

User = get_user_model()


_STATUS_LABELS = {
    'active': 'Aktif',
    'beta': 'Beta',
    'roadmap': 'Yol haritası',
}


class AdminApplicationsView(SuperuserRequiredMixin, TemplateView):
    """Sistemdeki uygulama modülleri ve panel eşlemesi (salt okunur)."""

    template_name = 'users/yonetim/applications.html'

    def get_context_data(self, **kwargs):
        from common.panel_registry import SHELL_LABELS, application_rows

        context = super().get_context_data(**kwargs)
        rows = []
        for row in application_rows(self.request):
            mod = row['module']
            panel = row['panel'] or {}
            rows.append({
                **row,
                'panel': panel,
                'shell_label': SHELL_LABELS.get(panel.get('shell', ''), panel.get('shell', '')),
                'status': mod.get('status', ''),
                'status_label': _STATUS_LABELS.get(mod.get('status', ''), mod.get('status', '')),
            })
        context['applications'] = rows
        return context


class AdminPanelsView(SuperuserRequiredMixin, TemplateView):
    """Marka panelleri ve barındırdıkları uygulamalar."""

    template_name = 'users/yonetim/panels.html'

    def get_context_data(self, **kwargs):
        from common.panel_registry import panel_rows

        context = super().get_context_data(**kwargs)
        context['panels'] = panel_rows(self.request)
        return context


class AdminPlanListView(SuperuserRequiredMixin, ListView):
    model = Plan
    template_name = 'users/yonetim/plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        return Plan.objects.annotate(owner_count=Count('users', distinct=True)).order_by('price')


class AdminPlanCreateView(SuperuserRequiredMixin, CreateView):
    model = Plan
    form_class = AdminPlanForm
    template_name = 'users/yonetim/plan_form.html'
    success_url = reverse_lazy('admin_plans')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Plan oluşturuldu.')
        return super().form_valid(form)


class AdminPlanUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Plan
    form_class = AdminPlanForm
    template_name = 'users/yonetim/plan_form.html'
    success_url = reverse_lazy('admin_plans')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Plan güncellendi.')
        return super().form_valid(form)


class AdminBillingInvoiceListView(SuperuserRequiredMixin, ListView):
    model = BillingInvoice
    template_name = 'users/yonetim/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 25

    def get_queryset(self):
        qs = BillingInvoice.objects.select_related('user', 'plan').order_by('-created_at')
        status = self.request.GET.get('durum', '').strip()
        if status in ('paid', 'pending'):
            qs = qs.filter(status=status)
        user_raw = self.request.GET.get('kullanici', '').strip()
        if user_raw.isdigit():
            qs = qs.filter(user_id=int(user_raw))
        return qs

    def get_context_data(self, **kwargs):
        from common.brand_team import production_users_queryset

        context = super().get_context_data(**kwargs)
        context['filter_users'] = production_users_queryset().exclude(is_superuser=True).order_by('username')[:200]
        context['active_status_filter'] = self.request.GET.get('durum', '')
        context['active_user_filter'] = self.request.GET.get('kullanici', '')
        return context


class AdminBillingInvoiceCreateView(SuperuserRequiredMixin, CreateView):
    model = BillingInvoice
    form_class = AdminBillingInvoiceForm
    template_name = 'users/yonetim/invoice_form.html'
    success_url = reverse_lazy('admin_invoices')

    def form_valid(self, form):
        messages.success(self.request, 'Fatura kaydı oluşturuldu.')
        return super().form_valid(form)


class AdminSiteSettingsView(SuperuserRequiredMixin, UpdateView):
    model = SiteSettings
    form_class = AdminSiteSettingsForm
    template_name = 'users/yonetim/settings.html'
    success_url = reverse_lazy('admin_site_settings')

    def get_object(self, queryset=None):
        obj, _ = SiteSettings.objects.get_or_create(pk=1)
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Site ayarları güncellendi.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['landing_preview_url'] = '/'
        return context


class AdminAuditLogView(SuperuserRequiredMixin, TemplateView):
    template_name = 'users/yonetim/audit_log.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['platform_logs'] = PlatformAuditLog.objects.select_related(
            'actor', 'brand', 'target_user',
        )[:100]
        context['impersonation_logs'] = ImpersonationAudit.objects.select_related(
            'actor', 'target',
        )[:50]
        return context


class AdminUsageReportExportView(SuperuserRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        for row in usage_report_csv_rows():
            writer.writerow(row)
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="plan-kullanim-raporu.csv"'
        return response


class AdminUsersExportView(SuperuserRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        from users.admin_views import production_users_queryset

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['Kullanıcı adı', 'Ad', 'E-posta', 'Süper admin', 'Aktif', 'Plan', 'Rol'])
        for user in production_users_queryset().select_related('plan', 'role').order_by('username'):
            writer.writerow([
                user.username,
                user.display_name,
                user.email,
                'evet' if user.is_superuser else 'hayır',
                'evet' if user.is_active else 'hayır',
                user.plan.name if user.plan_id else '',
                user.role.name if user.role_id else '',
            ])
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="platform-kullanicilar.csv"'
        return response
