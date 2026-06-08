"""Restoran dikeyi kayıt ve yönetim paneli kurulumu."""

from __future__ import annotations

from common.brand_scope import set_active_brand
from common.panel_registry import PANEL_KOBIPOS, panel_by_id
from common.panel_routing import (
    is_restaurant_brand,
    is_restaurant_plan,
    resolve_brand_panel_url,
    restaurant_panel_url,
)

__all__ = (
    'RESTAURANT_VERTICAL_SLUG',
    'RESTAURANT_MODULE_SLUG',
    'RESTAURANT_PANEL_URL',
    'apply_restaurant_owner_setup',
    'brand_panel_url',
    'is_restaurant_brand',
    'is_restaurant_plan',
    'setup_restaurant_signup',
)
from restaurant.compat import ensure_restaurant_tenant

RESTAURANT_VERTICAL_SLUG = 'restoran_kafe'
RESTAURANT_MODULE_SLUG = 'restaurant'
_kobipos = panel_by_id(PANEL_KOBIPOS) or {}
RESTAURANT_PANEL_URL = _kobipos.get('path_prefix', '/restoran/')


def brand_panel_url(brand, *, owner=None) -> str:
    """Marka için varsayılan panel yolu — KobiPOS veya KobiOPS."""
    return resolve_brand_panel_url(brand, owner=owner)


def apply_restaurant_owner_setup(user, brand, request=None) -> str:
    """Restoran aboneliği: tenant, modül, profil ve isteğe bağlı oturum markası."""
    from common.module_plan import plan_included_modules
    from core_settings.models import SiteSettings
    from users.utils import get_or_create_user_profile

    profile = get_or_create_user_profile(user)
    profile.restaurant_role = 'store_owner'
    profile.restaurant_brand = brand
    profile.save(update_fields=['restaurant_role', 'restaurant_brand'])

    ensure_restaurant_tenant(brand, owner=user)

    plan_mods = plan_included_modules(user.active_plan)
    if plan_mods:
        user.enabled_module_slugs = plan_mods
    else:
        slugs = list(user.enabled_module_slugs or [])
        if RESTAURANT_MODULE_SLUG not in slugs:
            slugs.append(RESTAURANT_MODULE_SLUG)
        user.enabled_module_slugs = slugs
    user.save(update_fields=['enabled_module_slugs'])

    settings = SiteSettings.objects.first()
    if settings:
        settings.primary_vertical_slug = RESTAURANT_VERTICAL_SLUG
        mod_slugs = list(settings.enabled_module_slugs or [])
        if RESTAURANT_MODULE_SLUG not in mod_slugs:
            mod_slugs.append(RESTAURANT_MODULE_SLUG)
            settings.enabled_module_slugs = mod_slugs
        settings.save(update_fields=['primary_vertical_slug', 'enabled_module_slugs'])

    from common.plan_sync import sync_brand_plan_from_owner

    sync_brand_plan_from_owner(user, brand)

    if request is not None:
        set_active_brand(request, brand.pk)
    return restaurant_panel_url(request)


def setup_restaurant_signup(request, user, brand):
    """Kayıt sonrası restoran modülü, tenant profili ve yönlendirme."""
    return apply_restaurant_owner_setup(user, brand, request=request)
