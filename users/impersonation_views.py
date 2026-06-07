from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View

from common.brand_access import resolve_post_login_url
from common.brand_team import subscription_owners_queryset
from .impersonation import ImpersonationError, is_impersonating, start_impersonation, stop_impersonation
from .mixins import SuperuserRequiredMixin

User = get_user_model()


class ImpersonateStartView(SuperuserRequiredMixin, View):
    """POST — hedef kullanıcı olarak panele geç."""

    def post(self, request, pk):
        if is_impersonating(request):
            messages.error(request, 'Zaten başka bir kullanıcı olarak oturum açtınız. Önce görünümden çıkın.')
            return redirect('home')

        target = get_object_or_404(subscription_owners_queryset(), pk=pk)
        try:
            start_impersonation(request, target)
        except ImpersonationError as exc:
            messages.error(request, str(exc))
            return redirect('admin_users')

        role = target.role_label
        messages.warning(
            request,
            f'"{target.display_name}" ({role}) olarak sistemi inceliyorsunuz. '
            f'Üst çubuktan süper admin oturumunuza dönebilirsiniz.',
        )
        return redirect(resolve_post_login_url(request, target))


class ImpersonateStopView(LoginRequiredMixin, View):
    """POST — süper admin hesabına dön."""

    login_url = reverse_lazy('login')

    def post(self, request):
        actor, previous = stop_impersonation(request)
        if not actor:
            messages.info(request, 'Aktif kullanıcı geçişi yok.')
            return redirect('home')

        prev_label = getattr(previous, 'display_name', '') or ''
        messages.success(
            request,
            f'Kullanıcı görünümü sonlandırıldı. Tekrar "{actor.display_name}" olarak oturum açtınız.'
            + (f' (Önceki: {prev_label})' if prev_label else ''),
        )
        return redirect('admin_dashboard')
