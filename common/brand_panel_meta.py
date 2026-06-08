"""Marka → panel meta verisi (badge, yedek, admin listeleri)."""

from __future__ import annotations

from common.panel_registry import SHELL_LABELS, apps_for_panel, panel_by_id
from common.panel_routing import resolve_brand_panel, resolve_brand_panel_id


def brand_panel_id(brand, owner=None) -> str:
    return resolve_brand_panel_id(brand, owner=owner)


def resolve_brand_panel_meta(brand, owner=None) -> dict:
    from common.brand_team import subscription_owner_for_brand

    if owner is None:
        owner = subscription_owner_for_brand(brand)
    panel_id = brand_panel_id(brand, owner=owner)
    panel = resolve_brand_panel(brand, owner=owner) or panel_by_id(panel_id) or {}
    theme = panel.get('theme') or {}
    return {
        'panel_id': panel_id,
        'panel_name': panel.get('name', ''),
        'path_prefix': panel.get('path_prefix', '/'),
        'icon': panel.get('icon', 'layout-grid'),
        'shell_label': SHELL_LABELS.get(panel.get('shell', ''), panel.get('shell', '')),
        'theme': theme,
        'app_count': len(apps_for_panel(panel_id)),
        'is_restaurant': panel_id == 'kobipos',
    }
