"""Platform (üst panel) ve bayi paneli erişim kuralları."""

from __future__ import annotations

from django.http import HttpRequest
from django.urls import reverse

from common.panel_registry import panel_by_id, panel_path_prefixes
from common.panel_routing import (
    is_restaurant_plan,
    resolve_brand_panel_url,
    restaurant_panel_url,
)
from core_settings.models import BrandMembership, BusinessBrand


PLATFORM_PANEL_PREFIXES = panel_path_prefixes()

_kobiops = panel_by_id('kobiops') or {}
DEALER_BLOCKED_PREFIXES = (_kobiops.get('path_prefix', '/panel/'),)


def user_owns_hq_brand(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return BrandMembership.objects.filter(
        user=user,
        brand__panel_kind=BusinessBrand.PANEL_HQ,
        role=BrandMembership.ROLE_OWNER,
        brand__is_active=True,
    ).exists()


def user_is_dealer_only(user) -> bool:
    """Yalnızca bayi panellerine üye; merkez ekibi veya üst panel sahibi değil."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user_owns_hq_brand(user):
        return False
    has_hq_access = BrandMembership.objects.filter(
        user=user,
        brand__panel_kind=BusinessBrand.PANEL_HQ,
        brand__is_active=True,
    ).exists()
    if has_hq_access:
        return False
    return BrandMembership.objects.filter(
        user=user,
        brand__panel_kind=BusinessBrand.PANEL_DEALER,
        brand__is_active=True,
    ).exists()


def user_can_access_platform_panel(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return False
    if user_is_dealer_only(user):
        return False
    return user.has_perm_codename('access.home')


def dealer_default_brand(user):
    from core_settings.models import BrandMembership

    mem = (
        BrandMembership.objects.filter(
            user=user,
            brand__panel_kind=BusinessBrand.PANEL_DEALER,
            brand__is_active=True,
        )
        .select_related('brand', 'brand__parent_brand')
        .order_by('joined_at')
        .first()
    )
    return mem.brand if mem else None


def resolve_post_login_url(request: HttpRequest, user) -> str:
    from common.tenant import build_brand_public_url

    tenant = getattr(request, 'tenant_brand', None)
    if tenant and not user.is_superuser:
        from common.brand_scope import _brand_id_allowed_for_user

        if not _brand_id_allowed_for_user(user, tenant.pk):
            return reverse('login')

    if user_is_dealer_only(user):
        brand = tenant or dealer_default_brand(user)
        if brand:
            base = build_brand_public_url(brand, request).rstrip('/')
            if user.has_perm_codename('access.services'):
                return f'{base}/services-dashboard/'
            if user.has_perm_codename('access.contact'):
                return f'{base}/contact/'
            if user.has_perm_codename('access.accounting'):
                return f'{base}/muhasebe/'
            return base + '/'

    if user.is_superuser:
        return reverse('admin_dashboard')

    from common.brand_scope import default_brand_for_user, get_active_brand_id
    from core_settings.models import BusinessBrand

    brand = None
    brand_id = get_active_brand_id(request)
    if brand_id:
        brand = BusinessBrand.objects.filter(pk=brand_id, is_active=True).first()
    if not brand:
        brand = default_brand_for_user(user)

    if brand:
        target = resolve_brand_panel_url(brand, owner=user, request=request)
        if target != reverse('home'):
            return target

    if is_restaurant_plan(user.active_plan):
        return restaurant_panel_url(request)

    return reverse('home')


def path_blocked_for_dealer(path: str) -> bool:
    for prefix in DEALER_BLOCKED_PREFIXES:
        if path == prefix.rstrip('/') or path.startswith(prefix):
            return True
    return False
