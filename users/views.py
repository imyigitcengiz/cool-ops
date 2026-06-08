from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import TemplateView, View

from common.brand_access import resolve_post_login_url, user_is_dealer_only
from common.brand_scope import create_brand_for_user, set_active_brand, _brand_id_allowed_for_user
from common.login_throttle import clear_login_attempts, is_login_blocked, register_failed_login
from common.register_throttle import is_register_blocked, register_attempt
from common.tenant import build_brand_public_url, tenant_login_url
from common.plan_sync import DEFAULT_TRIAL_DAYS, plan_trial_days
from core_settings.models import Plan, BillingInvoice

from .forms import UserLoginForm, UserPasswordChangeForm, UserProfileForm
from .register_form import UserRegisterForm
from .utils import get_or_create_user_profile


class UserLoginView(AuthLoginView):
    template_name = 'users/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST' and is_login_blocked(request):
            messages.error(
                request,
                'Çok fazla başarısız giriş denemesi. Lütfen 15 dakika sonra tekrar deneyin.',
            )
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = getattr(self.request, 'tenant_brand', None)
        context['tenant_brand'] = tenant
        context['is_dealer_login'] = bool(tenant and tenant.panel_kind == 'dealer')
        context['is_tenant_login'] = bool(tenant)
        return context

    def get_success_url(self):
        redirect_to = self.request.POST.get('next') or self.request.GET.get('next')
        user = self.request.user

        if redirect_to:
            if url_has_allowed_host_and_scheme(
                redirect_to,
                allowed_hosts={self.request.get_host()},
                require_https=self.request.is_secure(),
            ):
                return redirect_to

        return resolve_post_login_url(self.request, user)

    def form_invalid(self, form):
        register_failed_login(self.request)
        return super().form_invalid(form)

    def form_valid(self, form):
        user = form.get_user()
        tenant = getattr(self.request, 'tenant_brand', None)

        if tenant and not _brand_id_allowed_for_user(user, tenant.pk):
            register_failed_login(self.request)
            messages.error(self.request, 'Bu panele erişim yetkiniz yok.')
            return self.form_invalid(form)

        if not tenant and user_is_dealer_only(user):
            register_failed_login(self.request)
            brand = user.brand_memberships.filter(
                brand__panel_kind='dealer',
                brand__is_active=True,
            ).select_related('brand').first()
            login_url = build_brand_public_url(brand.brand, self.request).rstrip('/') + '/giris/' if brand else tenant_login_url(self.request)
            messages.error(
                self.request,
                'Bayi hesapları yalnızca kendi panel adresinden giriş yapabilir.',
            )
            return redirect(login_url)

        clear_login_attempts(self.request, form.cleaned_data.get('username', ''))
        messages.success(self.request, f'Hoş geldiniz, {user.display_name}.')
        return super().form_valid(form)


class UserLogoutView(AuthLogoutView):
    next_page = reverse_lazy('landing')

    def dispatch(self, request, *args, **kwargs):
        from users.impersonation import SESSION_IMPERSONATE_USER_ID, SESSION_IMPERSONATOR_KEY

        if request.method == 'POST':
            request.session.pop(SESSION_IMPERSONATE_USER_ID, None)
            request.session.pop(SESSION_IMPERSONATOR_KEY, None)
        response = super().dispatch(request, *args, **kwargs)
        if request.method == 'POST':
            messages.info(request, 'Oturum kapatıldı.')
        return response


class ProfileSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile_settings.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_or_create_user_profile(self.request.user)
        context['profile'] = profile
        context['profile_form'] = UserProfileForm(instance=profile, user=self.request.user)
        context['password_form'] = UserPasswordChangeForm(user=self.request.user)
        context['active_plan'] = self.request.user.active_plan
        return context

    def post(self, request, *args, **kwargs):
        profile = get_or_create_user_profile(request.user)
        action = request.POST.get('form_action', 'profile')

        if action == 'password':
            password_form = UserPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Şifreniz güncellendi.')
            else:
                messages.error(request, 'Şifre güncellenemedi. Lütfen alanları kontrol edin.')
            return redirect('profile_settings')

        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user,
        )
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profil bilgileriniz kaydedildi.')
        else:
            messages.error(request, 'Profil güncellenemedi. Lütfen alanları kontrol edin.')
        return redirect('profile_settings')


class UserRegisterView(View):
    def _registration_blocked(self, request):
        tenant = getattr(request, 'tenant_brand', None)
        if tenant:
            messages.info(
                request,
                'Üyelik yalnızca ana platform adresinden açılabilir. Bayi panelleri için yöneticiniz hesap oluşturur.',
            )
            return True
        return False

    def _resolve_plan(self, plan_id):
        if not plan_id:
            return Plan.objects.filter(is_active=True, price=0).order_by('price').first()
        return Plan.objects.filter(pk=plan_id, is_active=True).first()

    def _is_restaurant_vertical(self, request):
        return request.GET.get('vertical') == 'restaurant' or request.POST.get('vertical') == 'restaurant'

    def _restaurant_trial_days(self, plans, selected_plan=None):
        if selected_plan:
            return plan_trial_days(selected_plan)
        for plan in plans:
            if plan.price == 0:
                return plan_trial_days(plan)
        return DEFAULT_TRIAL_DAYS

    def _register_context(self, form, selected_plan=None, request=None):
        vertical = 'restaurant' if request and self._is_restaurant_vertical(request) else 'kobi'
        plans = Plan.objects.filter(is_active=True).order_by('price')
        if vertical == 'restaurant':
            plans = [
                p for p in plans
                if p.price == 0 or 'restaurant' in (p.included_module_slugs or [])
            ]
        trial_days = self._restaurant_trial_days(plans, selected_plan) if vertical == 'restaurant' else None
        return {
            'form': form,
            'selected_plan': selected_plan,
            'plans': plans.distinct(),
            'register_vertical': vertical,
            'register_trial_days': trial_days,
            'register_title': (
                f'KobiPOS — {trial_days} gün ücretsiz deneme'
                if vertical == 'restaurant'
                else 'Kobi Hub — Üye ol'
            ),
            'register_lead': (
                f'{trial_days} gün ücretsiz deneme ile menü, masa ve sipariş yönetimine hemen başlayın.'
                if vertical == 'restaurant'
                else 'Modüler operasyon panelinizi dakikalar içinde kurun.'
            ),
        }

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        if self._registration_blocked(request):
            return redirect('login')
        plan_id = request.GET.get('plan')
        selected_plan = self._resolve_plan(plan_id) if plan_id else None
        if plan_id and not selected_plan:
            messages.warning(request, 'Seçilen plan bulunamadı; ücretsiz paketle devam edebilirsiniz.')
        form = UserRegisterForm()
        return render(request, 'users/register.html', self._register_context(form, selected_plan, request))

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        if self._registration_blocked(request):
            return redirect('login')
        if is_register_blocked(request):
            messages.error(
                request,
                'Çok fazla kayıt denemesi. Lütfen bir saat sonra tekrar deneyin.',
            )
            return redirect('register')
        register_attempt(request)
        form = UserRegisterForm(request.POST)
        plan_id = request.POST.get('plan_id') or request.POST.get('plan_pick')
        selected_plan = self._resolve_plan(plan_id)

        if form.is_valid():
            from users.models import Role

            user = form.save(commit=False)
            admin_role = Role.objects.filter(slug='admin').first()
            if admin_role:
                user.role = admin_role
            if selected_plan:
                user.plan = selected_plan
            user.save()

            if selected_plan and selected_plan.price > 0:
                BillingInvoice.objects.create(
                    user=user,
                    plan=selected_plan,
                    amount=selected_plan.price,
                    status='paid',
                )

            get_or_create_user_profile(user)
            brand = create_brand_for_user(user, form.cleaned_data['brand_name'])

            redirect_url = 'home'
            if self._is_restaurant_vertical(request):
                from restaurant.onboarding import setup_restaurant_signup
                redirect_url = setup_restaurant_signup(request, user, brand)
            else:
                set_active_brand(request, brand.pk)

            login(request, user)
            messages.success(
                request,
                f'Hesabınız ve "{brand.name}" markanız oluşturuldu. Hoş geldiniz!',
            )
            return redirect(redirect_url)

        return render(request, 'users/register.html', self._register_context(form, selected_plan, request))

