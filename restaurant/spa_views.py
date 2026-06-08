"""React SPA barındırma — /restoran/ altı."""

from pathlib import Path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.views import View

from common.panel_registry import PANEL_KOBIPOS, panel_by_id

SPA_ROOT = Path(settings.BASE_DIR) / 'restaurant' / 'static' / 'restaurant-spa'
SPA_INDEX = SPA_ROOT / 'index.html'
SPA_ASSETS = SPA_ROOT / 'assets'

_kobipos = panel_by_id(PANEL_KOBIPOS) or {}
_RESTAURANT_PANEL_PREFIX = _kobipos.get('path_prefix', '/restoran/')


class RestaurantSpaView(LoginRequiredMixin, View):
    login_url = f'/giris/?next={_RESTAURANT_PANEL_PREFIX}'

    def get(self, request, asset_path='', spa_path=None):
        if asset_path:
            file_path = SPA_ASSETS / asset_path
            if file_path.is_file():
                return FileResponse(open(file_path, 'rb'))
            raise Http404()

        static_name = (spa_path or '').strip('/')
        if static_name in ('favicon.svg', 'icons.svg'):
            file_path = SPA_ROOT / static_name
            if file_path.is_file():
                return FileResponse(open(file_path, 'rb'))
            raise Http404()

        if not SPA_INDEX.is_file():
            from django.shortcuts import render
            return render(request, 'restaurant/hub.html', {
                'spa_missing': True,
            })
        return FileResponse(open(SPA_INDEX, 'rb'), content_type='text/html')
