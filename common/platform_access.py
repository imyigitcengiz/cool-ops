"""Süper admin ile marka / kiracı paneli erişim ayrımı."""

from __future__ import annotations

from django.http import HttpRequest

from common.panel_registry import panel_by_id, panel_path_prefixes
from users.impersonation import get_real_user, is_impersonating

_kobiops = panel_by_id('kobiops') or {}
BRAND_PLATFORM_PREFIX = _kobiops.get('path_prefix', '/panel/')

# Impersonate yokken süper admin yalnızca bu öneklerde dolaşabilir.
SUPERUSER_PLATFORM_PREFIXES = (
    '/yonetim/',
    '/profil/',
    '/api/bildirimler/',
    '/api/hizli-arama/',
    '/healthz/',
    '/cikis/',
    '/bilgi-bankasi/',
)

# Eski URL'ler — süper panele yönlendirir, middleware izin verir.
SUPERUSER_LEGACY_PREFIXES = (
    '/ayarlar/yedekler/',
)

# Kiracı modül yolları (marka kapsamı).
TENANT_MODULE_PREFIXES = (
    *panel_path_prefixes(),
    '/contact/',
    '/muhasebe/',
    '/services-dashboard/',
    '/tools/',
    '/crm/',
    '/sales-lead/',
    '/iletisim/',
    '/ortak/',
    '/ayarlar/',
    '/chat/',
    '/media/',
)


def _path_matches(path: str, prefix: str) -> bool:
    return path == prefix.rstrip('/') or path.startswith(prefix)


def path_is_brand_platform(path: str) -> bool:
    return _path_matches(path, BRAND_PLATFORM_PREFIX)


def path_is_tenant_module(path: str) -> bool:
    return any(_path_matches(path, prefix) for prefix in TENANT_MODULE_PREFIXES)


def path_is_superuser_platform(path: str) -> bool:
    if path in ('/cikis/', '/cikis'):
        return True
    if any(_path_matches(path, prefix) for prefix in SUPERUSER_LEGACY_PREFIXES):
        return True
    return any(_path_matches(path, prefix) for prefix in SUPERUSER_PLATFORM_PREFIXES)


def superuser_is_testing_tenant(request: HttpRequest) -> bool:
    return is_impersonating(request) and get_real_user(request).is_superuser


def bare_superuser(request: HttpRequest) -> bool:
    """Impersonate yokken oturumdaki süper admin."""
    user = get_real_user(request)
    return bool(user.is_authenticated and user.is_superuser and not is_impersonating(request))


def bare_superuser_blocked_from_path(request: HttpRequest, path: str) -> bool:
    """Süper admin kiracı/marka panellerine doğrudan erişemez — marka incele veya impersonate."""
    if not bare_superuser(request):
        return False
    if path_is_superuser_platform(path):
        return False
    if path in ('/', ''):
        return False
    if path_is_tenant_module(path) or path_is_brand_platform(path):
        return True
    return False
