"""KobiOPS User.plan ↔ KobiPOS RestaurantTenantProfile.plan_tier senkronu."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

DEFAULT_TRIAL_DAYS = 14
DEFAULT_BILLING_DAYS = 30

RESTAURANT_TIER_CHOICES = ('starter', 'growth', 'enterprise')
TEST_STORE_RESTAURANT_TIER = 'enterprise'

TIER_DISPLAY = {
    'starter': 'Starter',
    'growth': 'Growth',
    'enterprise': 'Enterprise',
}


def plan_trial_days(plan) -> int:
    if not plan:
        return DEFAULT_TRIAL_DAYS
    days = getattr(plan, 'trial_days', None)
    return days if days else DEFAULT_TRIAL_DAYS


def plan_billing_days(plan) -> int:
    if not plan:
        return DEFAULT_BILLING_DAYS
    days = getattr(plan, 'billing_days', None)
    return days if days else DEFAULT_BILLING_DAYS


def billing_days_for_restaurant_tier(tier: str, owner=None) -> int:
    if owner and getattr(owner, 'active_plan', None):
        return plan_billing_days(owner.active_plan)
    from core_settings.models import Plan

    plan = Plan.objects.filter(restaurant_plan_tier=tier, is_active=True).order_by('pk').first()
    if not plan:
        plan = Plan.objects.filter(name__icontains=tier, is_active=True).order_by('pk').first()
    return plan_billing_days(plan)


def extend_brand_subscription(brand, days: int) -> None:
    from common.panel_routing import is_restaurant_brand
    from restaurant.compat import get_tenant_profile

    if not brand or not is_restaurant_brand(brand) or days <= 0:
        return
    tenant = get_tenant_profile(brand)
    today = timezone.localdate()
    if tenant.plan_expiry and tenant.plan_expiry >= today:
        tenant.plan_expiry = tenant.plan_expiry + timedelta(days=days)
    else:
        tenant.plan_expiry = today + timedelta(days=days)
    tenant.save(update_fields=['plan_expiry'])


def kobiops_plan_to_tier(plan) -> str:
    if not plan:
        return 'starter'
    tier = (getattr(plan, 'restaurant_plan_tier', '') or '').strip().lower()
    if tier in RESTAURANT_TIER_CHOICES:
        return tier
    name = (getattr(plan, 'name', '') or '').lower()
    for candidate in RESTAURANT_TIER_CHOICES:
        if candidate in name:
            return candidate
    return 'starter'


def _brand_is_restaurant(brand, owner) -> bool:
    from common.panel_routing import is_restaurant_brand, is_restaurant_plan

    return is_restaurant_brand(brand) or is_restaurant_plan(getattr(owner, 'active_plan', None))


def sync_brand_plan_from_owner(owner, brand) -> None:
    """Abonelik sahibinin KobiOPS planını marka tenant planına yazar."""
    if not owner or owner.is_superuser or not brand:
        return
    if not _brand_is_restaurant(brand, owner):
        return

    from restaurant.compat import ensure_restaurant_tenant, get_tenant_profile
    from restaurant.models import RestaurantProfile

    ensure_restaurant_tenant(brand, owner=owner)
    if brand.is_test_store:
        tier = TEST_STORE_RESTAURANT_TIER
    else:
        tier = kobiops_plan_to_tier(owner.active_plan)
    tenant = get_tenant_profile(brand)
    if tenant.plan_tier != tier:
        tenant.plan_tier = tier
        tenant.save(update_fields=['plan_tier'])
    RestaurantProfile.objects.filter(brand=brand).update(
        active_plan=TIER_DISPLAY.get(tier, 'Starter'),
    )


def sync_owner_brands_from_plan(owner) -> None:
    """Sahip olduğu HQ markalarının tenant planlarını günceller."""
    if not owner or owner.is_superuser:
        return
    from core_settings.models import BrandMembership, BusinessBrand

    brand_ids = BrandMembership.objects.filter(
        user=owner,
        role=BrandMembership.ROLE_OWNER,
        brand__is_active=True,
        brand__panel_kind=BusinessBrand.PANEL_HQ,
    ).values_list('brand_id', flat=True)
    billing_days = plan_billing_days(owner.active_plan)
    for brand in BusinessBrand.objects.filter(pk__in=brand_ids):
        sync_brand_plan_from_owner(owner, brand)
        extend_brand_subscription(brand, billing_days)


def _ensure_catalog_role(slug: str):
    """Katalogdaki sistem rolünü (izinleriyle) döndürür."""
    from users.models import Role
    from users.permission_catalog import DEFAULT_ROLES

    data = DEFAULT_ROLES.get(slug)
    if not data:
        return None

    role_field_names = {f.name for f in Role._meta.get_fields()}
    defaults = {
        'name': data['name'],
        'description': data['description'],
        'is_system': data.get('is_system', False),
    }
    if 'scope' in role_field_names:
        defaults['scope'] = data.get('scope', Role.SCOPE_TENANT_CUSTOM)
    if 'app_id' in role_field_names:
        defaults['app_id'] = data.get('app_id', '')

    role, _ = Role.objects.get_or_create(slug=slug, defaults=defaults)
    if not role.permissions.exists():
        from users.permission_sync import sync_permissions_to_db

        perm_map = sync_permissions_to_db()
        role.permissions.set([perm_map[c] for c in data['permissions'] if c in perm_map])
    return role


def premium_plan_for_test_store(panel_id: str):
    """Test mağazası önizlemesi için en yüksek abonelik planı."""
    from core_settings.models import Plan

    from common.module_plan import plan_included_modules

    if panel_id == 'kobipos':
        plan = (
            Plan.objects.filter(
                restaurant_plan_tier=TEST_STORE_RESTAURANT_TIER,
                is_active=True,
            )
            .order_by('-price')
            .first()
        )
        if plan:
            return plan
        return (
            Plan.objects.filter(is_active=True, name__icontains='Enterprise')
            .order_by('-price')
            .first()
        )

    plan = Plan.objects.filter(is_active=True, name='Kurumsal Plan').first()
    if plan:
        return plan
    for candidate in Plan.objects.filter(is_active=True).order_by('-price'):
        mods = set(plan_included_modules(candidate))
        if mods <= {'restaurant', 'settings'}:
            continue
        return candidate
    return Plan.objects.filter(is_active=True).order_by('-price').first()


def apply_test_store_premium_plan(brand, owner=None) -> None:
    """Test mağazası ve sahibi her zaman üst plan + tam modül erişimi kullanır."""
    if not brand or not brand.is_test_store:
        return

    from common.brand_panel_meta import brand_panel_id
    from common.brand_team import subscription_owner_for_brand
    from common.module_plan import clamp_owner_modules_to_plan
    from common.panel_routing import is_restaurant_brand

    owner = owner or subscription_owner_for_brand(brand)
    if not owner or owner.is_superuser:
        return

    panel_id = brand_panel_id(brand, owner=owner)
    plan = premium_plan_for_test_store(panel_id)
    if plan and owner.plan_id != plan.pk:
        owner.plan = plan
        owner.save(update_fields=['plan_id'])
    clamp_owner_modules_to_plan(owner)

    if panel_id == 'kobipos' or is_restaurant_brand(brand):
        role = _ensure_catalog_role('restaurant_access')
        if role and owner.role_id != role.pk:
            owner.role = role
            owner.save(update_fields=['role_id'])
        from users.utils import get_or_create_user_profile

        profile = get_or_create_user_profile(owner)
        profile.restaurant_role = 'store_owner'
        profile.restaurant_brand = brand
        profile.save(update_fields=['restaurant_role', 'restaurant_brand'])
    else:
        role = _ensure_catalog_role('admin')
        if role and owner.role_id != role.pk:
            owner.role = role
            owner.save(update_fields=['role_id'])
        from users.utils import get_or_create_user_profile

        profile = get_or_create_user_profile(owner)
        if profile.restaurant_brand_id or profile.restaurant_role:
            profile.restaurant_role = ''
            profile.restaurant_brand = None
            profile.save(update_fields=['restaurant_role', 'restaurant_brand'])

    if panel_id == 'kobipos' or is_restaurant_brand(brand):
        from restaurant.compat import ensure_restaurant_tenant, get_tenant_profile
        from restaurant.models import RestaurantProfile

        ensure_restaurant_tenant(brand, owner=owner)
        tenant = get_tenant_profile(brand)
        updates = []
        if tenant.plan_tier != TEST_STORE_RESTAURANT_TIER:
            tenant.plan_tier = TEST_STORE_RESTAURANT_TIER
            updates.append('plan_tier')
        far_expiry = timezone.localdate() + timedelta(days=3650)
        if tenant.plan_expiry != far_expiry:
            tenant.plan_expiry = far_expiry
            updates.append('plan_expiry')
        if updates:
            tenant.save(update_fields=updates)
        RestaurantProfile.objects.filter(brand=brand).update(
            active_plan=TIER_DISPLAY.get(TEST_STORE_RESTAURANT_TIER, 'Enterprise'),
        )


def sync_owner_plan_from_tier(owner, tier: str) -> None:
    """KobiPOS ödeme sonrası tenant tier → KobiOPS Plan eşlemesi."""
    if not owner or owner.is_superuser:
        return
    tier = (tier or 'starter').lower()
    if tier not in RESTAURANT_TIER_CHOICES:
        return
    from core_settings.models import Plan

    plan = Plan.objects.filter(restaurant_plan_tier=tier, is_active=True).order_by('pk').first()
    if not plan:
        plan = Plan.objects.filter(name__icontains=tier, is_active=True).order_by('pk').first()
    if plan and owner.plan_id != plan.pk:
        owner.plan = plan
        owner.save(update_fields=['plan_id'])
        from common.module_plan import clamp_owner_modules_to_plan

        clamp_owner_modules_to_plan(owner)
