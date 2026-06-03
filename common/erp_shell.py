"""Tek panel kabuk — aktif modül ve tema."""

from __future__ import annotations

from common.module_runtime import resolve_path_module_slug

_SHELL_THEMES: dict[str | None, str] = {
    'panel': 'erp-theme-sky',
    'contact': 'erp-theme-violet',
    'services': 'erp-theme-sky',
    'accounting': 'erp-theme-emerald',
    'outreach': 'erp-theme-blue',
    'settings': 'erp-theme-amber',
    'tools': 'erp-theme-sky',
    None: 'erp-theme-sky',
}


def resolve_erp_shell_module(path: str) -> str | None:
    """Şablonlar için aktif modül slug'ı (panel, contact, …)."""
    if path.startswith('/yonetim/'):
        return 'admin'
    if path.startswith('/panel'):
        return 'panel'
    if path.startswith('/tools/'):
        slug = resolve_path_module_slug(path)
        return slug or 'tools'
    return resolve_path_module_slug(path)


def erp_shell_theme_for_module(slug: str | None) -> str:
    if slug == 'admin':
        return 'erp-theme-sky'
    return _SHELL_THEMES.get(slug, 'erp-theme-sky')


def build_erp_shell_context(request) -> dict:
    from common.module_runtime import (
        build_erp_sidebar_modules,
        build_erp_sidebar_tools,
        resolve_sidebar_expand_slug,
    )

    path = getattr(request, 'path', '') or ''
    slug = resolve_erp_shell_module(path)
    expand_slug = resolve_sidebar_expand_slug(path, slug, request)
    user = getattr(request, 'user', None)
    sidebar_modules = []
    sidebar_tools = None
    if user and user.is_authenticated:
        sidebar_modules = build_erp_sidebar_modules(user, request, active_slug=expand_slug)
        sidebar_tools = build_erp_sidebar_tools(user, request, expand_slug=expand_slug)
    return {
        'erp_active_module': slug,
        'erp_sidebar_expand': expand_slug,
        'erp_shell_theme': erp_shell_theme_for_module(slug),
        'erp_sidebar_modules': sidebar_modules,
        'erp_sidebar_tools': sidebar_tools,
    }
