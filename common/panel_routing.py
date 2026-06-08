"""Merkezi panel yönlendirme — marka ve plan bazlı panel çözümlemesi."""

from __future__ import annotations

from django.http import HttpRequest
from django.urls import reverse

from common.panel_registry import (
    DEFAULT_PANEL_ID,
    PANEL_KOBIPOS,
    PANEL_KOBIOPS,
    panel_by_id,
    panel_url,
)

RESTAURANT_MODULE_SLUG = 'restaurant'


def is_restaurant_plan(plan) -> bool:
    """Plan restoran dikeyi (KobiPOS) için mi?

    Restoran planlarında `restaurant` modülü vardır; KobiOPS saha panelinin ayırt edici
    modülü `services` (Yardım Masası) yoktur.
    """
    if not plan:
        return False
    from common.module_plan import plan_included_modules

    mods = set(plan_included_modules(plan))
    if RESTAURANT_MODULE_SLUG not in mods:
        return False
    return 'services' not in mods


def is_restaurant_brand(brand) -> bool:
    if not brand:
        return False
    from restaurant.models import RestaurantTenantProfile

    return RestaurantTenantProfile.objects.filter(brand=brand).exists()


def resolve_plan_default_panel(plan) -> str:
    return PANEL_KOBIPOS if is_restaurant_plan(plan) else PANEL_KOBIOPS


def resolve_brand_panel(brand, owner=None) -> dict:
    """Marka için hedef panel kaydı."""
    if is_restaurant_brand(brand):
        return panel_by_id(PANEL_KOBIPOS) or panel_by_id(DEFAULT_PANEL_ID)
    if brand and getattr(brand, 'is_test_store', False):
        return panel_by_id(PANEL_KOBIOPS) or panel_by_id(DEFAULT_PANEL_ID)
    if owner and is_restaurant_plan(
        getattr(owner, 'active_plan', None) or getattr(owner, 'plan', None)
    ):
        return panel_by_id(PANEL_KOBIPOS) or panel_by_id(DEFAULT_PANEL_ID)
    return panel_by_id(PANEL_KOBIOPS) or panel_by_id(DEFAULT_PANEL_ID)


def resolve_brand_panel_id(brand, owner=None) -> str:
    return resolve_brand_panel(brand, owner=owner)['id']


def resolve_brand_panel_url(brand, owner=None, request=None) -> str:
    panel = resolve_brand_panel(brand, owner=owner)
    return panel_url(panel['id'], request)


def restaurant_panel_url(request=None) -> str:
    return panel_url(PANEL_KOBIPOS, request)


def kobiops_panel_url(request=None) -> str:
    return panel_url(PANEL_KOBIOPS, request)
