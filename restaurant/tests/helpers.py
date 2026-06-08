"""Restoran API test yardımcıları — KobiHub marka ve oturum kurulumu."""

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from common.brand_scope import create_brand_for_user
from core_settings.models import BrandMembership
from restaurant.compat import ensure_restaurant_tenant
from users.models import Role
from users.utils import get_or_create_user_profile

User = get_user_model()
API_PREFIX = '/restoran/api/'


def api_url(path: str) -> str:
    path = path if path.startswith('/') else f'/{path}'
    if path.startswith(API_PREFIX):
        return path
    return f'{API_PREFIX}{path.lstrip("/")}'


def _ensure_admin_role():
    role, _ = Role.objects.get_or_create(
        slug='admin',
        defaults={'name': 'Admin', 'is_system': True},
    )
    return role


def _configure_user(user, *, role=None):
    user.role = role or _ensure_admin_role()
    user.enabled_module_slugs = ['restaurant', 'settings']
    user.save()


def create_restaurant_owner(
    username,
    password='pass12345',
    brand_name='Test Brand',
    *,
    plan='starter',
    plan_expiry=None,
):
    user = User.objects.create_user(username=username, password=password)
    _configure_user(user)
    brand = create_brand_for_user(user, brand_name, bypass_plan_limit=True)
    tenant = ensure_restaurant_tenant(brand)
    tenant.plan_tier = plan
    if plan_expiry is not None:
        tenant.plan_expiry = plan_expiry
    tenant.save()
    profile = get_or_create_user_profile(user)
    profile.restaurant_role = 'store_owner'
    profile.restaurant_brand = brand
    profile.save()
    token = Token.objects.create(user=user)
    return user, brand, token


def create_restaurant_staff(owner, brand, username, password='pass12345', restaurant_role='waiter'):
    user = User.objects.create_user(username=username, password=password)
    _configure_user(user)
    BrandMembership.objects.get_or_create(user=user, brand=brand, defaults={'role': 'member'})
    profile = get_or_create_user_profile(user)
    profile.restaurant_role = restaurant_role
    profile.restaurant_brand = brand
    profile.save()
    return user, profile


def authenticate_client(client, token, brand):
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    session = client.session
    session['active_brand_id'] = brand.pk
    session.save()
