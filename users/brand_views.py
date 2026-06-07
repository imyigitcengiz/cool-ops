from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View

from common.brand_scope import set_active_brand


class BrandSwitchView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')

    def post(self, request):
        raw = request.POST.get('brand_id')
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse_lazy('home')
        try:
            brand_id = int(raw)
        except (TypeError, ValueError):
            messages.error(request, 'Geçersiz marka seçimi.')
            return redirect(next_url)
        if set_active_brand(request, brand_id):
            messages.success(request, 'Aktif marka güncellendi.')
        else:
            messages.error(request, 'Bu markaya erişiminiz yok.')
        return redirect(next_url)
