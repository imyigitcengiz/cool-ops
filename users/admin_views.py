from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, FormView

from common.brand_scope import set_active_brand
from core_settings.models import BusinessBrand

from .admin_forms import (
    AdminBrandCreateForm,
    AdminBrandUpdateForm,
    AdminPlatformUserCreateForm,
    AdminRoleForm,
    AdminUserUpdateForm,
    RoleForm,
)
from .admin_services import (
    admin_user_delete_context,
    brand_delete_context,
    brand_hierarchy_rows,
    membership_matrix_rows,
    parse_membership_post,
    platform_dashboard_stats,
    platform_relations_context,
    platform_summary_stats,
    purge_and_delete_brand,
    reassign_brand_owner,
    strip_superuser_brand_memberships,
    sync_user_brand_memberships,
    tenant_usage_rows,
)
from .mixins import PlatformStaffRequiredMixin, SuperuserRequiredMixin
from .models import Permission, Role

User = get_user_model()


def production_users_queryset():
    """RBAC test hesaplarını yönetim listelerinden gizler."""
    from common.brand_team import production_users_queryset as _qs
    return _qs()


class SuperAdminDashboardView(SuperuserRequiredMixin, TemplateView):
    template_name = 'users/yonetim/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = platform_dashboard_stats()
        context.update(stats)
        context['total_roles'] = Role.objects.filter(scope=Role.SCOPE_PLATFORM_SYSTEM).count()
        context['summary'] = platform_summary_stats()
        from common.brand_team import subscription_owners_queryset
        from core_settings.models import BrandMembership

        owners = subscription_owners_queryset()
        context['recent_users'] = owners[:8]
        for user in context['recent_users']:
            user.admin_owned_brands = [
                m.brand
                for m in user.brand_memberships.all()
                if m.role == BrandMembership.ROLE_OWNER
            ]
        try:
            from restaurant.models import RestaurantBranch, RestaurantTenantProfile
            context['restaurant_tenant_count'] = RestaurantTenantProfile.objects.count()
            context['restaurant_branch_count'] = RestaurantBranch.objects.count()
            context['restaurant_franchise_panels'] = RestaurantBranch.objects.filter(
                panel_enabled=True, is_active=True,
            ).count()
        except Exception:
            context['restaurant_tenant_count'] = 0
            context['restaurant_branch_count'] = 0
            context['restaurant_franchise_panels'] = 0
        return context


def _attach_admin_owned_brands(users):
    from core_settings.models import BrandMembership

    for user in users:
        memberships = list(user.brand_memberships.all())
        user.admin_brand_memberships = memberships
        user.admin_owned_brands = [
            m.brand
            for m in memberships
            if m.role == BrandMembership.ROLE_OWNER
        ]


class AdminBrandInspectView(PlatformStaffRequiredMixin, View):
    """Süper admin / test yetkilisi — marka sahibi olarak inceleme (impersonation)."""

    @staticmethod
    def _inspect_fail_redirect(request):
        from common.platform_test_access import is_platform_test_inspector
        from users.impersonation import get_real_user

        actor = get_real_user(request)
        if is_platform_test_inspector(actor) and not actor.is_superuser:
            return redirect('admin_panels')
        return redirect('admin_brands')

    def post(self, request, pk):
        brand = get_object_or_404(BusinessBrand, pk=pk, is_active=True)
        from common.brand_team import subscription_owner_for_brand
        from common.panel_routing import is_restaurant_brand, is_restaurant_plan, resolve_brand_panel_url
        from common.platform_test_access import can_inspect_brand
        from restaurant.onboarding import apply_restaurant_owner_setup
        from users.impersonation import ImpersonationError, get_real_user, start_impersonation

        actor = get_real_user(request)
        ok, reason = can_inspect_brand(actor, brand)
        if not ok:
            messages.error(request, reason)
            return self._inspect_fail_redirect(request)

        owner = subscription_owner_for_brand(brand)
        if not owner:
            messages.error(request, 'Bu markanın tanımlı bir abonelik sahibi yok.')
            return self._inspect_fail_redirect(request)

        try:
            start_impersonation(request, owner, brand=brand)
        except ImpersonationError as exc:
            messages.error(request, str(exc))
            return self._inspect_fail_redirect(request)

        if not set_active_brand(request, brand.pk):
            messages.error(request, 'Marka oturumu başlatılamadı.')
            return redirect('admin_users')

        if is_restaurant_brand(brand) or is_restaurant_plan(owner.active_plan):
            apply_restaurant_owner_setup(owner, brand, request=request)

        from users.platform_audit import log_platform_audit
        from users.models import PlatformAuditLog

        log_platform_audit(
            request,
            action=PlatformAuditLog.ACTION_BRAND_INSPECT,
            brand=brand,
            detail=f'{brand.name} (sahip: {owner.username})',
        )
        messages.success(
            request,
            f'"{brand.name}" markası {owner.get_full_name() or owner.username} olarak inceleniyor.',
        )
        next_url = (request.POST.get('next') or '').strip()
        if next_url.startswith('/'):
            return redirect(next_url)
        return redirect(resolve_brand_panel_url(brand, owner=owner, request=request))


class RoleListView(SuperuserRequiredMixin, ListView):
    model = Role
    template_name = 'users/yonetim/role_list.html'
    context_object_name = 'roles'

    def get_queryset(self):
        from django.db.models import Count

        qs = Role.objects.annotate(user_count=Count('users')).order_by('name')
        tab = (self.request.GET.get('tab') or 'system').strip()
        if tab == 'app':
            return qs.filter(scope=Role.SCOPE_APP_PRESET)
        if tab == 'tenant':
            return qs.filter(scope=Role.SCOPE_TENANT_CUSTOM)
        return qs.filter(scope=Role.SCOPE_PLATFORM_SYSTEM)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = (self.request.GET.get('tab') or 'system').strip()
        if context['active_tab'] not in ('system', 'app', 'tenant'):
            context['active_tab'] = 'system'
        return context


class RoleFormMixin:
    def _selected_permission_ids(self):
        if getattr(self, 'object', None) and self.object.pk:
            return set(self.object.permissions.values_list('id', flat=True))
        return set()

    def _permission_ids_from_post(self):
        return [
            int(value)
            for value in self.request.POST.getlist('permissions')
            if str(value).isdigit()
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            kwargs['permission_ids'] = self._permission_ids_from_post()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['selected_permission_ids'] = set(self._permission_ids_from_post())
        else:
            context['selected_permission_ids'] = self._selected_permission_ids()
        access_permissions = Permission.objects.filter(
            kind=Permission.KIND_ACCESS,
        ).order_by('sort_order', 'name')
        action_permissions = Permission.objects.filter(
            kind=Permission.KIND_ACTION,
        ).order_by('module', 'sort_order', 'name')
        action_by_module = {}
        for perm in action_permissions:
            action_by_module.setdefault(perm.module, []).append(perm)
        context['access_permissions'] = access_permissions
        context['action_permissions_by_module'] = action_by_module
        role = getattr(self, 'object', None)
        if role and role.pk:
            locked = role.scope in (Role.SCOPE_PLATFORM_SYSTEM, Role.SCOPE_APP_PRESET)
            context['role_can_delete'] = not locked and not role.users.exists()
            context['role_delete_blocked_reason'] = ''
            if locked:
                context['role_delete_blocked_reason'] = 'Platform ve uygulama şablonları silinemez.'
            elif role.users.exists():
                context['role_delete_blocked_reason'] = f'Bu role atanmış {role.users.count()} kullanıcı var.'
        else:
            context['role_can_delete'] = False
            context['role_delete_blocked_reason'] = ''
        return context


class RoleCreateView(SuperuserRequiredMixin, RoleFormMixin, CreateView):
    model = Role
    form_class = AdminRoleForm
    template_name = 'users/yonetim/role_form.html'
    success_url = reverse_lazy('admin_roles')

    def form_valid(self, form):
        scope = form.cleaned_data.get('scope')
        form.instance.is_system = scope in (Role.SCOPE_PLATFORM_SYSTEM, Role.SCOPE_APP_PRESET)
        if scope == Role.SCOPE_PLATFORM_SYSTEM:
            form.instance.app_id = ''
        messages.success(self.request, 'Rol oluşturuldu.')
        return super().form_valid(form)

    def get_success_url(self):
        scope = self.object.scope
        if scope == Role.SCOPE_APP_PRESET:
            return f'{reverse("admin_roles")}?tab=app'
        if scope == Role.SCOPE_PLATFORM_SYSTEM:
            return f'{reverse("admin_roles")}?tab=system'
        return reverse('admin_roles')


class RoleUpdateView(SuperuserRequiredMixin, RoleFormMixin, UpdateView):
    model = Role
    form_class = AdminRoleForm
    template_name = 'users/yonetim/role_form.html'
    success_url = reverse_lazy('admin_roles')

    def form_valid(self, form):
        if self.object.scope in (Role.SCOPE_PLATFORM_SYSTEM, Role.SCOPE_APP_PRESET):
            form.instance.slug = self.object.slug
            form.instance.scope = self.object.scope
            form.instance.app_id = self.object.app_id
        messages.success(self.request, 'Rol güncellendi.')
        return super().form_valid(form)

    def get_success_url(self):
        if self.object.scope == Role.SCOPE_APP_PRESET:
            return f'{reverse("admin_roles")}?tab=app'
        if self.object.scope == Role.SCOPE_TENANT_CUSTOM:
            return f'{reverse("admin_roles")}?tab=tenant'
        return f'{reverse("admin_roles")}?tab=system'


class RoleDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Role
    template_name = 'users/yonetim/role_confirm_delete.html'
    success_url = reverse_lazy('admin_roles')

    def get_queryset(self):
        return Role.objects.filter(scope=Role.SCOPE_TENANT_CUSTOM)

    def delete(self, request, *args, **kwargs):
        role = self.get_object()
        if role.scope != Role.SCOPE_TENANT_CUSTOM:
            messages.error(request, 'Yalnızca abonelik özel rolleri silinebilir.')
            return redirect('admin_roles')
        if role.users.exists():
            messages.error(request, 'Bu role atanmış kullanıcılar var; silinemez.')
            return redirect('admin_roles')
        messages.info(request, f'"{role.name}" rolü silindi.')
        return super().delete(request, *args, **kwargs)


class AdminUserListView(SuperuserRequiredMixin, ListView):
    model = User
    template_name = 'users/yonetim/user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        from core_settings.models import BrandMembership

        qs = production_users_queryset().order_by('-date_joined').prefetch_related(
            'brand_memberships__brand',
            'role',
            'plan',
        )
        user_type = self.request.GET.get('tur', '').strip()
        if user_type == 'owner':
            owner_ids = BrandMembership.objects.filter(
                role=BrandMembership.ROLE_OWNER,
                brand__is_active=True,
            ).values_list('user_id', flat=True)
            qs = qs.filter(Q(pk__in=owner_ids) | Q(plan__isnull=False)).distinct()
        elif user_type == 'member':
            owner_ids = BrandMembership.objects.filter(
                role=BrandMembership.ROLE_OWNER,
            ).values_list('user_id', flat=True)
            qs = qs.filter(brand_memberships__isnull=False).exclude(
                is_superuser=True,
            ).exclude(pk__in=owner_ids).distinct()
        elif user_type == 'superuser':
            qs = qs.filter(is_superuser=True)

        brand_raw = self.request.GET.get('marka', '').strip()
        if brand_raw.isdigit():
            qs = qs.filter(brand_memberships__brand_id=int(brand_raw)).distinct()

        status = self.request.GET.get('durum', '').strip()
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _attach_admin_owned_brands(context.get('users', []))
        for user in context.get('users', []):
            user.admin_delete_ctx = admin_user_delete_context(self.request.user, user)
        context['filter_brands'] = BusinessBrand.objects.filter(is_active=True).order_by('name')
        context['active_type_filter'] = self.request.GET.get('tur', '')
        context['active_brand_filter'] = self.request.GET.get('marka', '')
        context['active_status_filter'] = self.request.GET.get('durum', '')
        return context


class AdminUserCreateView(SuperuserRequiredMixin, CreateView):
    model = User
    form_class = AdminPlatformUserCreateForm
    template_name = 'users/yonetim/user_form.html'
    success_url = reverse_lazy('admin_users')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        from common.brand_scope import create_brand_for_user
        from common.brand_team import attach_user_to_brand

        user = form.save()
        from .utils import get_or_create_user_profile

        get_or_create_user_profile(user)
        account_type = form.cleaned_data['account_type']
        if account_type == AdminPlatformUserCreateForm.ACCOUNT_SUPERUSER:
            messages.success(
                self.request,
                f'Platform yöneticisi "{user.display_name}" oluşturuldu.',
            )
            return redirect(self.success_url)
        if account_type == AdminPlatformUserCreateForm.ACCOUNT_OWNER:
            brand_name = form.cleaned_data['brand_name']
            try:
                brand = create_brand_for_user(user, brand_name, bypass_plan_limit=True)
            except ValueError as exc:
                user.delete()
                form.add_error('brand_name', str(exc))
                return self.form_invalid(form)
            from common.panel_routing import is_restaurant_plan
            from restaurant.onboarding import apply_restaurant_owner_setup

            if is_restaurant_plan(user.active_plan):
                apply_restaurant_owner_setup(user, brand, request=self.request)
                messages.success(
                    self.request,
                    f'Abonelik sahibi "{user.display_name}" ve KobiPOS markası "{brand.name}" oluşturuldu.',
                )
            else:
                messages.success(
                    self.request,
                    f'Abonelik sahibi "{user.display_name}" ve marka "{brand.name}" oluşturuldu.',
                )
            return redirect(self.success_url)

        brand = form.cleaned_data['brand']
        attach_user_to_brand(
            user,
            brand,
            membership_role=form.cleaned_data['membership_role'],
            is_default=True,
        )
        messages.success(
            self.request,
            f'"{user.display_name}" kullanıcısı "{brand.name}" markasına eklendi.',
        )
        return redirect(self.success_url)


class AdminUserUpdateView(SuperuserRequiredMixin, UpdateView):
    model = User
    form_class = AdminUserUpdateForm
    template_name = 'users/yonetim/user_form.html'
    success_url = reverse_lazy('admin_users')

    def get_queryset(self):
        return production_users_queryset()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['editor'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        if user.is_superuser:
            strip_superuser_brand_memberships(user)
        else:
            brand_roles, default_brand_id = parse_membership_post(self.request)
            sync_user_brand_memberships(
                user,
                brand_roles=brand_roles,
                default_brand_id=default_brand_id,
            )
        messages.success(self.request, 'Kullanıcı güncellendi.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        from core_settings.models import BrandMembership

        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['membership_roles'] = BrandMembership.ROLE_CHOICES
        if self.object and self.object.pk:
            context['current_memberships'] = list(
                self.object.brand_memberships.select_related('brand').order_by('brand__name')
            )
        context.update(admin_user_delete_context(self.request.user, self.object))
        return context


class AdminUserDeleteView(SuperuserRequiredMixin, DeleteView):
    model = User
    template_name = 'users/yonetim/user_confirm_delete.html'
    success_url = reverse_lazy('admin_users')

    def get_queryset(self):
        return production_users_queryset().exclude(is_superuser=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin_user_delete_context(self.request.user, self.object))
        return context

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        ctx = admin_user_delete_context(request.user, user)
        if not ctx['user_can_delete']:
            messages.error(request, ctx['user_delete_blocked_reason'])
            return redirect('admin_users')
        return super().get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        ctx = admin_user_delete_context(request.user, user)
        if not ctx['user_can_delete']:
            messages.error(request, ctx['user_delete_blocked_reason'])
            return redirect('admin_users')
        label = user.display_name
        messages.info(request, f'"{label}" kullanıcısı silindi.')
        return super().delete(request, *args, **kwargs)


class AdminBrandListView(SuperuserRequiredMixin, ListView):
    model = BusinessBrand
    template_name = 'users/yonetim/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 25

    def get_queryset(self):
        from core_settings.models import BrandMembership

        qs = (
            BusinessBrand.objects.select_related('parent_brand', 'created_by')
            .prefetch_related(
                Prefetch(
                    'memberships',
                    queryset=BrandMembership.objects.filter(
                        role=BrandMembership.ROLE_OWNER,
                    ).select_related('user'),
                    to_attr='owner_memberships',
                )
            )
            .order_by('name')
        )
        show = self.request.GET.get('durum', 'active').strip()
        if show == 'active':
            qs = qs.filter(is_active=True)
        elif show == 'inactive':
            qs = qs.filter(is_active=False)
        kind = self.request.GET.get('tur', '').strip()
        if kind in (BusinessBrand.PANEL_HQ, BusinessBrand.PANEL_DEALER):
            qs = qs.filter(panel_kind=kind)
        panel = self.request.GET.get('panel', '').strip()
        if panel in ('kobiops', 'kobipos'):
            from restaurant.models import RestaurantTenantProfile

            kobipos_ids = RestaurantTenantProfile.objects.values_list('brand_id', flat=True)
            if panel == 'kobipos':
                qs = qs.filter(pk__in=kobipos_ids)
            else:
                qs = qs.exclude(pk__in=kobipos_ids)
        return qs

    def get_context_data(self, **kwargs):
        from common.brand_panel_meta import resolve_brand_panel_meta

        context = super().get_context_data(**kwargs)
        for brand in context.get('brands', []):
            owners = getattr(brand, 'owner_memberships', [])
            brand.owner_user = owners[0].user if owners else brand.created_by
            brand.panel_meta = resolve_brand_panel_meta(brand, owner=brand.owner_user)
        context['active_status_filter'] = self.request.GET.get('durum', 'active')
        context['active_kind_filter'] = self.request.GET.get('tur', '')
        context['active_panel_filter'] = self.request.GET.get('panel', '')
        return context


class AdminBrandCreateView(SuperuserRequiredMixin, FormView):
    form_class = AdminBrandCreateForm
    template_name = 'users/yonetim/brand_form.html'
    success_url = reverse_lazy('admin_brands')

    def get_context_data(self, **kwargs):
        from common.tenant import get_tenant_base_domain

        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        context['tenant_base_domain'] = get_tenant_base_domain()
        return context

    def form_valid(self, form):
        from common.brand_scope import create_brand_for_user
        from core_settings.models import BusinessBrand

        owner = form.cleaned_data['owner']
        panel_kind = form.cleaned_data['panel_kind']
        parent = form.cleaned_data.get('parent_brand')
        try:
            brand = create_brand_for_user(
                owner,
                form.cleaned_data['name'],
                panel_kind=panel_kind,
                parent_brand=parent if panel_kind == BusinessBrand.PANEL_DEALER else None,
                tenant_routing=form.cleaned_data['tenant_routing'],
                host_slug=form.cleaned_data.get('host_slug', ''),
                legal_name=form.cleaned_data.get('legal_name', ''),
                phone=form.cleaned_data.get('phone', ''),
                bypass_plan_limit=True,
            )
        except ValueError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f'"{brand.name}" markası "{owner.display_name}" hesabına eklendi.',
        )
        return redirect(self.success_url)


class AdminBrandDetailView(SuperuserRequiredMixin, TemplateView):
    template_name = 'users/yonetim/brand_detail.html'

    def get_context_data(self, **kwargs):
        from core_settings.models import BrandMembership
        from common.tenant import build_brand_public_url, get_tenant_base_domain

        context = super().get_context_data(**kwargs)
        brand = get_object_or_404(
            BusinessBrand.objects.select_related('parent_brand', 'created_by', 'first_owner'),
            pk=self.kwargs['pk'],
        )
        memberships = (
            BrandMembership.objects.filter(brand=brand)
            .select_related('user', 'user__role')
            .order_by('role', 'user__username')
        )
        owner_mem = memberships.filter(role=BrandMembership.ROLE_OWNER).first()
        from customers.models import Customer

        from common.brand_panel_meta import resolve_brand_panel_meta

        owner_user = owner_mem.user if owner_mem else brand.created_by
        context['brand'] = brand
        context['memberships'] = memberships
        context['owner_user'] = owner_user
        context['panel_meta'] = resolve_brand_panel_meta(brand, owner=owner_user)
        context['first_owner_user'] = brand.first_owner
        context['dealer_panels'] = brand.dealer_panels.filter(is_active=True).order_by('name')
        context['tenant_url'] = build_brand_public_url(brand, self.request)
        context['tenant_key'] = brand.tenant_key
        context['tenant_base_domain'] = get_tenant_base_domain()
        context['user_count'] = memberships.count()
        context['customer_count'] = Customer.objects.filter(brand=brand).count()
        return context


class AdminBrandUpdateView(SuperuserRequiredMixin, UpdateView):
    model = BusinessBrand
    form_class = AdminBrandUpdateForm
    template_name = 'users/yonetim/brand_form.html'
    success_url = reverse_lazy('admin_brands')

    def get_queryset(self):
        return BusinessBrand.objects.all()

    def get_context_data(self, **kwargs):
        from common.tenant import build_brand_public_url, get_tenant_base_domain

        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['tenant_url'] = build_brand_public_url(self.object, self.request)
        context['tenant_base_domain'] = get_tenant_base_domain()
        context['tenant_key'] = self.object.tenant_key
        return context

    def get_success_url(self):
        return reverse_lazy('admin_brand_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        owner = form.cleaned_data.get('owner')
        if owner:
            reassign_brand_owner(self.object, owner)
        messages.success(self.request, f'"{form.instance.name}" markası güncellendi.')
        return response


class AdminBrandDeactivateView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        brand = get_object_or_404(BusinessBrand, pk=pk)
        brand.is_active = False
        brand.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, f'"{brand.name}" pasifleştirildi.')
        next_url = request.POST.get('next', '').strip()
        if next_url.startswith('/'):
            return redirect(next_url)
        return redirect('admin_brands')


class AdminBrandActivateView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        brand = get_object_or_404(BusinessBrand, pk=pk)
        brand.is_active = True
        brand.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, f'"{brand.name}" aktifleştirildi.')
        next_url = request.POST.get('next', '').strip()
        if next_url.startswith('/'):
            return redirect(next_url)
        return redirect('admin_brand_detail', pk=brand.pk)


class AdminBrandDeleteView(SuperuserRequiredMixin, DeleteView):
    model = BusinessBrand
    template_name = 'users/yonetim/brand_confirm_delete.html'
    success_url = reverse_lazy('admin_brands')

    def get_queryset(self):
        return BusinessBrand.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(brand_delete_context(self.object))
        return context

    def get(self, request, *args, **kwargs):
        brand = self.get_object()
        ctx = brand_delete_context(brand)
        if not ctx['brand_can_delete']:
            messages.error(request, ctx['brand_delete_blocked_reason'])
            return redirect('admin_brand_detail', pk=brand.pk)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        brand = self.get_object()
        ctx = brand_delete_context(brand)
        if not ctx['brand_can_delete']:
            messages.error(request, ctx['brand_delete_blocked_reason'])
            return redirect('admin_brand_detail', pk=brand.pk)

        confirm_name = (request.POST.get('confirm_name') or '').strip()
        if confirm_name != brand.name:
            messages.error(request, 'Onay için marka adını aynen yazın.')
            return redirect('admin_brand_delete', pk=brand.pk)

        if ctx['brand_requires_wipe'] and request.POST.get('confirm_wipe') != 'on':
            messages.error(request, 'Verilerle birlikte silmeyi onaylayın.')
            return redirect('admin_brand_delete', pk=brand.pk)

        try:
            name = purge_and_delete_brand(brand)
        except Exception as exc:
            messages.error(request, f'Marka silinemedi: {exc}')
            return redirect('admin_brand_detail', pk=kwargs['pk'])

        from users.platform_audit import log_platform_audit
        from users.models import PlatformAuditLog

        log_platform_audit(
            request,
            action=PlatformAuditLog.ACTION_BRAND_DELETE,
            detail=name,
        )
        messages.info(request, f'"{name}" markası kalıcı olarak silindi.')
        return redirect(self.success_url)


class AdminRelationsView(SuperuserRequiredMixin, TemplateView):
    template_name = 'users/yonetim/relations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(platform_relations_context())
        context['active_tab'] = self.request.GET.get('tab', 'ozet')
        return context


class AdminReportsView(SuperuserRequiredMixin, TemplateView):
    template_name = 'users/yonetim/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(platform_dashboard_stats())
        context['summary'] = platform_summary_stats()
        return context


class AdminUsageReportView(SuperuserRequiredMixin, TemplateView):
    template_name = 'users/yonetim/reports_usage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usage_rows'] = tenant_usage_rows()
        return context


class AdminSystemBackupView(SuperuserRequiredMixin, TemplateView):
    template_name = 'users/yonetim/system_backup.html'

    def get_context_data(self, **kwargs):
        from core_settings.backup import FACTORY_RESET_CONFIRM_PHRASE, backup_status_summary
        from core_settings.models import BusinessBrand

        context = super().get_context_data(**kwargs)
        from common.brand_panel_meta import resolve_brand_panel_meta

        context['backup_status'] = backup_status_summary()
        context['factory_reset_confirm_phrase'] = FACTORY_RESET_CONFIRM_PHRASE
        backup_brands = list(BusinessBrand.objects.filter(is_active=True).order_by('name'))
        for brand in backup_brands:
            brand.panel_meta = resolve_brand_panel_meta(brand)
        context['backup_brands'] = backup_brands
        from common.brand_team import subscription_owners_queryset

        context['backup_owners'] = subscription_owners_queryset().order_by('username')
        return context

    def post(self, request, *args, **kwargs):
        from core_settings.system_backup_handlers import handle_system_backup_post
        return handle_system_backup_post(request, redirect_name='admin_system_backup')


class AdminSystemUpdatesView(SuperuserRequiredMixin, TemplateView):
    template_name = 'users/yonetim/system_updates.html'

    def dispatch(self, request, *args, **kwargs):
        from common.panel_env import panel_git_updates_enabled
        from django.contrib import messages
        from django.shortcuts import redirect

        if not panel_git_updates_enabled():
            messages.info(
                request,
                'Panel içi güncelleme kapalı. Sunucuda git pull ve deploy script kullanın.',
            )
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from core_settings.updater import check_for_updates

        context = super().get_context_data(**kwargs)
        status = check_for_updates(force=False)
        context['update_status'] = status.to_dict()
        return context


class AdminSystemUpdateStatusApiView(SuperuserRequiredMixin, TemplateView):
    """GET — güncelleme durumu JSON."""

    def get(self, request, *args, **kwargs):
        from django.http import JsonResponse
        from core_settings.updater import check_for_updates

        force = request.GET.get('force') in ('1', 'true', 'yes')
        status = check_for_updates(force=force)
        return JsonResponse(status.to_dict())


class AdminSystemUpdateApplyApiView(SuperuserRequiredMixin, TemplateView):
    """POST — güncellemeyi uygula."""

    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        from core_settings.updater import apply_update, check_for_updates, schedule_restart

        status = check_for_updates(force=True)
        if not status.update_available:
            return JsonResponse({
                'ok': True,
                'message': 'Zaten güncelsiniz.',
                'steps': [],
                'restarting': False,
            })
        if not status.can_apply:
            return JsonResponse({
                'ok': False,
                'error': status.message or 'Güncelleme uygulanamıyor.',
                'steps': [],
            }, status=400)

        ok, msg, steps, restart = apply_update()
        if ok and restart:
            schedule_restart()
        return JsonResponse({
            'ok': ok,
            'message': msg,
            'steps': steps,
            'restarting': ok and restart,
            'apply_mode': status.apply_mode,
        }, status=200 if ok else 500)
