"""Test mağaza inceleme — platform personeli erişim kuralları."""

from __future__ import annotations

from django.contrib.auth import get_user_model

User = get_user_model()


def is_platform_test_inspector(user) -> bool:
    """Süper admin veya SiteSettings.test_store_inspectors listesindeki platform rolü."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    from users.models import Role

    role = getattr(user, 'role', None)
    if not role or role.scope != Role.SCOPE_PLATFORM_SYSTEM:
        return False
    from core_settings.models import SiteSettings

    settings = SiteSettings.objects.filter(pk=1).first()
    if not settings:
        return False
    return settings.test_store_inspectors.filter(pk=user.pk).exists()


def can_inspect_brand(actor, brand) -> tuple[bool, str]:
    if not actor or not actor.is_authenticated:
        return False, 'Giriş gerekli.'
    if not brand or not brand.is_active:
        return False, 'Marka aktif değil.'
    if actor.is_superuser:
        return True, ''
    if not is_platform_test_inspector(actor):
        return False, 'Bu işlem için yetkiniz yok.'
    if not brand.is_test_store:
        return False, 'Yalnızca test mağazaları incelenebilir.'
    return True, ''


LEGACY_DEMO_OWNER_USERNAME = '_platform_demo_owner'
DEMO_OWNER_USERNAME_BY_PANEL = {
    'kobiops': '_platform_demo_owner_kobiops',
    'kobipos': '_platform_demo_owner_kobipos',
}
# Geriye dönük uyumluluk
DEMO_OWNER_USERNAME = LEGACY_DEMO_OWNER_USERNAME


def demo_owner_username(panel_id: str) -> str:
    return DEMO_OWNER_USERNAME_BY_PANEL.get(panel_id, LEGACY_DEMO_OWNER_USERNAME)


def default_test_brand_for_panel(panel_id: str):
    from common.brand_panel_meta import brand_panel_id
    from core_settings.models import BusinessBrand, SiteSettings

    settings = SiteSettings.objects.filter(pk=1).first()
    if settings:
        if panel_id == 'kobiops' and settings.default_test_brand_kobiops_id:
            brand = settings.default_test_brand_kobiops
            if brand and brand.is_active:
                return brand
        if panel_id == 'kobipos' and settings.default_test_brand_kobipos_id:
            brand = settings.default_test_brand_kobipos
            if brand and brand.is_active:
                return brand

    for brand in BusinessBrand.objects.filter(is_active=True, is_test_store=True).order_by('pk'):
        if brand_panel_id(brand) == panel_id:
            return brand
    return None


def _get_or_create_demo_owner(panel_id: str = 'kobiops'):
    from common.plan_sync import premium_plan_for_test_store

    username = demo_owner_username(panel_id)
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'is_active': True},
    )
    if created:
        user.set_unusable_password()

    plan = premium_plan_for_test_store(panel_id)
    if plan:
        user.plan = plan
    user.save()
    return user


def _ensure_demo_brand_owner(brand, panel_id: str):
    """Test markanın paneline özel demo sahibini garanti eder (paylaşımlı eski sahip ayrılır)."""
    from common.brand_team import subscription_owner_for_brand
    from users.admin_services import reassign_brand_owner

    target = _get_or_create_demo_owner(panel_id)
    owner = subscription_owner_for_brand(brand)
    legacy_usernames = {
        LEGACY_DEMO_OWNER_USERNAME,
        *DEMO_OWNER_USERNAME_BY_PANEL.values(),
    }
    if owner and owner.username in legacy_usernames and owner.pk != target.pk:
        reassign_brand_owner(brand, target)
        owner = target
    elif not owner or owner.pk != target.pk:
        reassign_brand_owner(brand, target)
        owner = target
    from common.plan_sync import apply_test_store_premium_plan

    apply_test_store_premium_plan(brand, owner=owner)
    return owner


def ensure_default_test_brand_for_panel(panel_id: str):
    """Panel için test mağazası yoksa demo marka oluşturur ve SiteSettings'e bağlar."""
    from common.brand_scope import create_brand_for_user
    from common.panel_registry import PANEL_KOBIPOS, panel_by_id
    from core_settings.models import BusinessBrand, SiteSettings

    from common.plan_sync import apply_test_store_premium_plan

    existing = default_test_brand_for_panel(panel_id)
    if existing:
        _ensure_demo_brand_owner(existing, panel_id)
        return existing

    owner = _get_or_create_demo_owner(panel_id)
    panel = panel_by_id(panel_id) or {}
    brand_name = f"Demo {panel.get('name', panel_id)}"

    brand = create_brand_for_user(
        owner,
        brand_name,
        bypass_plan_limit=True,
    )
    brand.is_test_store = True
    brand.save(update_fields=['is_test_store'])

    if panel_id == PANEL_KOBIPOS:
        from restaurant.compat import ensure_restaurant_tenant

        ensure_restaurant_tenant(brand, owner=owner)

    settings, _ = SiteSettings.objects.get_or_create(pk=1, defaults={'site_name': 'Kobi Hub'})
    if panel_id == 'kobiops':
        settings.default_test_brand_kobiops = brand
        settings.save(update_fields=['default_test_brand_kobiops'])
    elif panel_id == PANEL_KOBIPOS:
        settings.default_test_brand_kobipos = brand
        settings.save(update_fields=['default_test_brand_kobipos'])

    _ensure_demo_brand_owner(brand, panel_id)
    return brand


def active_brand_count_for_panel(panel_id: str) -> int:
    from core_settings.models import BusinessBrand
    from restaurant.models import RestaurantTenantProfile

    if panel_id == 'kobipos':
        return BusinessBrand.objects.filter(
            is_active=True,
            pk__in=RestaurantTenantProfile.objects.values_list('brand_id', flat=True),
        ).count()
    return (
        BusinessBrand.objects.filter(is_active=True)
        .exclude(pk__in=RestaurantTenantProfile.objects.values_list('brand_id', flat=True))
        .count()
    )


def is_platform_staff_yonetim_path(path: str, method: str = 'GET') -> bool:
    if path == '/yonetim/paneller/' or path.startswith('/yonetim/paneller'):
        return True
    if path in ('/yonetim/paneller/test-gir/', '/yonetim/paneller/test-kapat/'):
        return True
    if method.upper() == 'POST' and '/yonetim/markalar/' in path and path.rstrip('/').endswith('/incele'):
        return True
    return False


def is_inspecting_test_store(request) -> bool:
    return bool(get_test_inspect_session(request)['active'])


def get_test_inspect_session(request) -> dict:
    """Açık test marka inceleme oturumu (impersonation + is_test_store marka)."""
    from common.brand_panel_meta import brand_panel_id
    from common.brand_scope import get_active_brand
    from users.impersonation import get_real_user, is_impersonating

    empty = {
        'active': False,
        'brand': None,
        'panel_id': '',
        'brand_name': '',
        'target_username': '',
        'target_display_name': '',
    }
    if not is_impersonating(request):
        return empty
    actor = get_real_user(request)
    if not is_platform_test_inspector(actor):
        return empty
    brand = get_active_brand(request)
    if not brand or not brand.is_test_store:
        return empty
    target = request.user
    return {
        'active': True,
        'brand': brand,
        'panel_id': brand_panel_id(brand, owner=target),
        'brand_name': brand.name,
        'target_username': getattr(target, 'username', '') or '',
        'target_display_name': getattr(target, 'display_name', '') or getattr(target, 'username', ''),
    }
