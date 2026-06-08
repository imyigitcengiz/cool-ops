"""BiDoluPos API uyumluluk — BusinessBrand ve KobiHub kullanıcı profili."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

RESTAURANT_ROLE_CHOICES = (
    ('super_admin', 'Süper Yönetici'),
    ('store_owner', 'Kurum Yöneticisi'),
    ('manager', 'Operasyon Müdürü'),
    ('waiter', 'Servis Sorumlusu'),
    ('cashier', 'Finans Sorumlusu'),
    ('kitchen', 'Üretim Sorumlusu'),
)


class RestaurantAPIProfile:
    """BiDoluPos UserProfile arayüzü — KobiHub UserProfile üzerine."""

    def __init__(self, user, request=None):
        self.user = user
        self._request = request
        self._base = getattr(user, 'profile', None)

    @property
    def role(self):
        from restaurant.api.security import is_api_superuser, normalize_restaurant_role

        base = self._base or self._ensure_base()
        stored = base.restaurant_role if base else ''
        return normalize_restaurant_role(stored, user=self.user)

    @role.setter
    def role(self, value):
        from restaurant.api.security import is_api_superuser

        if value == 'super_admin' and not is_api_superuser(self.user):
            value = 'store_owner'
        base = self._ensure_base()
        base.restaurant_role = value or ''
        base.save(update_fields=['restaurant_role'])

    @property
    def brand(self):
        base = self._base or self._ensure_base()
        if base.restaurant_brand_id:
            return base.restaurant_brand
        if self._request is not None:
            from common.brand_scope import get_active_brand
            brand = get_active_brand(self._request)
            if brand:
                return brand
        from common.brand_scope import default_brand_for_user
        return default_brand_for_user(self.user)

    @brand.setter
    def brand(self, value):
        base = self._ensure_base()
        base.restaurant_brand = value
        base.save(update_fields=['restaurant_brand'])

    @property
    def phone(self):
        return (self._base.phone if self._base else '') or ''

    @phone.setter
    def phone(self, value):
        base = self._ensure_base()
        base.phone = value
        base.save(update_fields=['phone'])

    @property
    def avatar(self):
        return self._base.avatar if self._base else None

    @avatar.setter
    def avatar(self, value):
        base = self._ensure_base()
        base.avatar = value
        base.save(update_fields=['avatar'])

    def _ensure_base(self):
        from users.utils import get_or_create_user_profile
        self._base = get_or_create_user_profile(self.user)
        return self._base

    def save(self, update_fields=None):
        if self._base:
            self._base.save(update_fields=update_fields)


def get_api_profile(user, request=None) -> RestaurantAPIProfile:
    return RestaurantAPIProfile(user, request)


def get_user_brand(user, request=None):
    from restaurant.api.security import is_api_superuser

    profile = get_api_profile(user, request)
    if is_api_superuser(user):
        return None
    return profile.brand


def get_tenant_profile(brand):
    """BusinessBrand için plan alanlarını döner (BiDoluPos Brand uyumu)."""
    from restaurant.models import RestaurantTenantProfile
    tenant, _ = RestaurantTenantProfile.objects.get_or_create(
        brand=brand,
        defaults={'plan_tier': 'starter'},
    )
    return tenant


def ensure_restaurant_tenant(brand, *, trial_days=14):
    from restaurant.models import RestaurantTenantProfile, RestaurantProfile
    tenant, created = RestaurantTenantProfile.objects.get_or_create(
        brand=brand,
        defaults={
            'plan_tier': 'starter',
            'plan_expiry': timezone.localdate() + timedelta(days=trial_days),
            'trial_started_at': timezone.now(),
            'public_slug': brand.slug,
        },
    )
    if created or not tenant.public_slug:
        tenant.public_slug = brand.slug
        tenant.save(update_fields=['public_slug'])
    RestaurantProfile.objects.get_or_create(
        brand=brand,
        defaults={'name': brand.name, 'website_slug': brand.slug},
    )
    return tenant


def brand_plan_tier(brand) -> str:
    tenant = get_tenant_profile(brand)
    return tenant.plan_tier


def brand_plan_expiry(brand):
    tenant = get_tenant_profile(brand)
    return tenant.plan_expiry


def serialize_brand_for_api(brand):
    from restaurant.api.plan_limits import get_plan_status, get_brand_usage, PLAN_LIMITS
    tenant = get_tenant_profile(brand)
    plan = tenant.plan_tier
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['starter'])
    usage = get_brand_usage(brand)
    plan_status = get_plan_status(brand)
    return {
        'id': brand.id,
        'name': brand.name,
        'slug': brand.slug,
        'plan': plan,
        'plan_expiry': str(tenant.plan_expiry) if tenant.plan_expiry else None,
        'is_active': brand.is_active,
        'limits': limits,
        'usage': usage,
        'plan_status': plan_status,
    }
