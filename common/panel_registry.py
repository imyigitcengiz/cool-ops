"""Marka panel kaydı — uygulama → panel eşlemesinin tek kaynağı."""

from __future__ import annotations

from django.urls import NoReverseMatch, reverse

from common.module_catalog import MODULE_KIND_APP, MODULES
from common.module_labels import PRODUCT_KOBIPOS, PRODUCT_KOBIOPS

PANEL_KOBIOPS = 'kobiops'
PANEL_KOBIPOS = 'kobipos'

DEFAULT_PANEL_ID = PANEL_KOBIOPS

SHELL_DJANGO_ERP = 'django_erp'
SHELL_REACT_SPA = 'react_spa'

PANELS: tuple[dict, ...] = (
    {
        'id': PANEL_KOBIOPS,
        'name': PRODUCT_KOBIOPS,
        'summary': 'Saha servis, rehber, yardım masası ve ön muhasebe — Django ERP paneli.',
        'path_prefix': '/panel/',
        'entry_url_name': 'home',
        'shell': SHELL_DJANGO_ERP,
        'icon': 'wrench',
        'sort': 10,
        'theme': {
            'accent': 'red',
            'icon_bg': 'bg-red-50',
            'icon_text': 'text-red-700',
            'badge_bg': 'bg-red-100',
            'badge_text': 'text-red-800',
            'border': 'border-red-200',
            'button_bg': 'bg-red-600',
            'button_hover': 'hover:bg-red-700',
        },
    },
    {
        'id': PANEL_KOBIPOS,
        'name': PRODUCT_KOBIPOS,
        'summary': 'Menü, masa, sipariş ve mutfak — React SPA restoran paneli.',
        'path_prefix': '/restoran/',
        'entry_url_name': 'restaurant_hub',
        'shell': SHELL_REACT_SPA,
        'icon': 'utensils',
        'sort': 20,
        'theme': {
            'accent': 'amber',
            'icon_bg': 'bg-amber-50',
            'icon_text': 'text-amber-700',
            'badge_bg': 'bg-amber-100',
            'badge_text': 'text-amber-800',
            'border': 'border-amber-200',
            'button_bg': 'bg-amber-600',
            'button_hover': 'hover:bg-amber-700',
        },
    },
)

SHELL_LABELS: dict[str, str] = {
    SHELL_DJANGO_ERP: 'Django ERP',
    SHELL_REACT_SPA: 'React SPA',
}


def all_panels() -> list[dict]:
    return [dict(p) for p in PANELS]


def panel_by_id(panel_id: str) -> dict | None:
    for panel in PANELS:
        if panel['id'] == panel_id:
            return dict(panel)
    return None


def panel_path_prefixes() -> tuple[str, ...]:
    return tuple(p['path_prefix'] for p in PANELS)


def panel_api_prefix(panel_id: str) -> str:
    panel = panel_by_id(panel_id)
    if not panel:
        return ''
    return f"{panel['path_prefix']}api/"


def panel_for_module(slug: str) -> dict | None:
    for mod in MODULES:
        if mod['slug'] == slug:
            panel_id = mod.get('panel_id', DEFAULT_PANEL_ID)
            return panel_by_id(panel_id)
    return None


def apps_for_panel(panel_id: str) -> list[dict]:
    apps = []
    for mod in MODULES:
        if mod['kind'] != MODULE_KIND_APP:
            continue
        if mod.get('panel_id', DEFAULT_PANEL_ID) == panel_id:
            apps.append(dict(mod))
    apps.sort(key=lambda m: (m.get('sort', 99), m['name']))
    return apps


def all_application_modules() -> list[dict]:
    apps = [dict(m) for m in MODULES if m['kind'] == MODULE_KIND_APP]
    apps.sort(key=lambda m: (m.get('sort', 99), m['name']))
    return apps


def franchise_panel_url(panel_slug: str | None) -> str | None:
    """Franchise giriş URL'si — KobiPOS panel öneki üzerinden."""
    if not panel_slug:
        return None
    panel = panel_by_id(PANEL_KOBIPOS)
    prefix = panel['path_prefix'] if panel else '/restoran/'
    return f'{prefix}franchise?code={panel_slug}'


def panel_url(panel_id: str, request=None) -> str:
    panel = panel_by_id(panel_id)
    if not panel:
        return '/'
    try:
        return reverse(panel['entry_url_name'])
    except NoReverseMatch:
        return panel['path_prefix']


def module_panel_url(slug: str, request=None) -> str:
    panel = panel_for_module(slug)
    if not panel:
        return '/'
    return panel_url(panel['id'], request)


def application_rows(request=None) -> list[dict]:
    """Admin uygulama listesi — modül + panel eşlemesi."""
    rows = []
    for mod in all_application_modules():
        panel = panel_for_module(mod['slug'])
        rows.append({
            'module': mod,
            'panel': panel,
            'panel_url': panel_url(panel['id'], request) if panel else '/',
        })
    return rows


def panel_rows(request=None) -> list[dict]:
    """Admin panel listesi — panel + barındırdığı uygulamalar."""
    from common.platform_test_access import (
        active_brand_count_for_panel,
        default_test_brand_for_panel,
    )

    rows = []
    for panel in all_panels():
        test_brand = default_test_brand_for_panel(panel['id'])
        rows.append({
            'panel': panel,
            'apps': apps_for_panel(panel['id']),
            'entry_url': panel_url(panel['id'], request),
            'shell_label': SHELL_LABELS.get(panel['shell'], panel['shell']),
            'theme': panel.get('theme') or {},
            'brand_count': active_brand_count_for_panel(panel['id']),
            'default_test_brand': test_brand,
        })
    return rows
