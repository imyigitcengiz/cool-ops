"""KobiOPS User.plan ↔ KobiPOS RestaurantTenantProfile.plan_tier senkronu."""

from __future__ import annotations

RESTAURANT_TIER_CHOICES = ('starter', 'growth', 'enterprise')

TIER_DISPLAY = {
    'starter': 'Starter',
    'growth': 'Growth',
    'enterprise': 'Enterprise',
}


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

    ensure_restaurant_tenant(brand)
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
    for brand in BusinessBrand.objects.filter(pk__in=brand_ids):
        sync_brand_plan_from_owner(owner, brand)


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
