#!/usr/bin/env python3
"""BiDoluPos API dosyalarını KobiHub restaurant/api yapısına uyarlar."""

from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / 'restaurant' / 'api'

REPLACEMENTS = [
    ('from django.contrib.auth.models import User', 'from django.contrib.auth import get_user_model\nUser = get_user_model()'),
    ('from .models import Brand', 'from core_settings.models import BusinessBrand as Brand'),
    ('Brand.objects', 'Brand.objects.filter(panel_kind=Brand.PANEL_HQ)'),
    ('from .models import', 'from restaurant.models import'),
    ('from .branch_scope import', 'from restaurant.api.tenant_scope import'),
    ('from .tenant_helpers import', 'from restaurant.api.tenant_helpers import'),
    ('from .serializers import', 'from restaurant.api.serializers import'),
    ('from .plan_limits import', 'from restaurant.api.plan_limits import'),
    ('from .plan_middleware import', 'from restaurant.api.plan_middleware import'),
    ('from .payment_service import', 'from restaurant.api.payment_service import'),
    ('from .franchise_ops import', 'from restaurant.api.franchise_ops import'),
    ('from .throttling import', 'from restaurant.api.throttling import'),
    ('from .models import UserProfile', 'from restaurant.compat import get_api_profile as _get_api_profile\n# UserProfile shim'),
    ('UserProfile.objects', '# UserProfile.objects — use get_api_profile'),
    ('getattr(user, \'profile\', None)', 'get_api_profile(user, request)'),
    ('getattr(request.user, \'profile\', None)', 'get_api_profile(request.user, request)'),
    ('getattr(self.request.user, \'profile\', None)', 'get_api_profile(self.request.user, self.request)'),
    ('profile, _ = UserProfile.objects.get_or_create(user=user)', 'profile = get_api_profile(user, request)'),
    ('profile, _ = UserProfile.objects.get_or_create(user=request.user)', 'profile = get_api_profile(request.user, request)'),
    ('caller_profile, _ = UserProfile.objects.get_or_create(user=request.user)', 'caller_profile = get_api_profile(request.user, request)'),
    ('caller_profile, _ = UserProfile.objects.get_or_create(user=self.request.user)', 'caller_profile = get_api_profile(self.request.user, self.request)'),
    ("return f'/franchise?code={obj.panel_slug}'", "return f'/restoran/franchise?code={obj.panel_slug}'"),
]

IMPORT_COMPAT = 'from restaurant.compat import get_api_profile, serialize_brand_for_api, ensure_restaurant_tenant, get_tenant_profile\n'


def adapt_file(path: Path):
    text = path.read_text(encoding='utf-8')
    if 'get_api_profile' not in text and path.name not in ('throttling.py', 'payment_service.py'):
        text = IMPORT_COMPAT + text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')


def main():
    for py in API_DIR.glob('*.py'):
        if py.name == '__init__.py':
            continue
        adapt_file(py)
    print('Adapted', len(list(API_DIR.glob('*.py'))) - 1, 'files')


if __name__ == '__main__':
    main()
