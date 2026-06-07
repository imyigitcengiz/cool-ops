from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View

from users.impersonation import get_real_user


class SettingsBackupRedirectView(LoginRequiredMixin, View):
    """Eski /ayarlar/yedekler/ — yalnızca süper admin süper panele yönlendirilir."""

    def get(self, request):
        user = get_real_user(request)
        if user.is_superuser:
            return redirect('admin_system_backup')
        messages.error(request, 'Yedekleme ve sıfırlama yalnızca süper admin panelindedir.')
        return redirect('home')

    def post(self, request):
        return self.get(request)
