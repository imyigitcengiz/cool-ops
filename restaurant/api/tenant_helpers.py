"""Tenant sahiplik doğrulama ve rol yönetimi."""

from rest_framework import status
from rest_framework.response import Response

from restaurant.api.security import is_api_superuser

STORE_OWNER_ASSIGNABLE_ROLES = frozenset({
    'manager', 'waiter', 'cashier', 'kitchen',
})
SUPERUSER_ASSIGNABLE_ROLES = frozenset({
    'store_owner', 'manager', 'waiter', 'cashier', 'kitchen',
})


def get_user_brand(user, request=None):
    from restaurant.compat import get_api_profile
    profile = get_api_profile(user, request)
    if is_api_superuser(user):
        return None
    return profile.brand


def validate_role_assignment(caller_user, caller_role, new_role):
    if new_role == 'super_admin':
        return False, 'super_admin rolü atanamaz.'
    if is_api_superuser(caller_user):
        allowed = SUPERUSER_ASSIGNABLE_ROLES
    elif caller_role == 'store_owner':
        allowed = STORE_OWNER_ASSIGNABLE_ROLES
    else:
        return False, 'Rol atama yetkiniz yok.'
    if new_role not in allowed:
        return False, f'"{new_role}" rolünü atama yetkiniz yok.'
    return True, None


def user_owns_brand(user, brand, request=None):
    if brand is None:
        return False
    from restaurant.compat import get_api_profile
    profile = get_api_profile(user, request)
    if is_api_superuser(user):
        return True
    user_brand = profile.brand
    return user_brand is not None and user_brand.pk == brand.pk


def deny_cross_tenant(user, obj_brand, request=None):
    if obj_brand is None:
        return Response({'error': 'Kayıt marka bilgisi içermiyor.'}, status=status.HTTP_400_BAD_REQUEST)
    if not user_owns_brand(user, obj_brand, request):
        return Response({'error': 'Bu kaynağa erişim yetkiniz yok.'}, status=status.HTTP_403_FORBIDDEN)
    return None


def get_tenant_table(user, table_id, request=None):
    from restaurant.models import Table
    try:
        table = Table.objects.select_related('brand').get(id=table_id)
    except Table.DoesNotExist:
        return None, Response({'error': 'Masa bulunamadı'}, status=status.HTTP_400_BAD_REQUEST)
    err = deny_cross_tenant(user, table.brand, request)
    if err:
        return None, err
    return table, None


def get_tenant_menu_item(user, menu_item_id, request=None):
    from restaurant.models import MenuItem
    try:
        item = MenuItem.objects.select_related('brand').get(id=menu_item_id)
    except MenuItem.DoesNotExist:
        return None, Response({'error': 'Menü ürünü bulunamadı'}, status=status.HTTP_400_BAD_REQUEST)
    err = deny_cross_tenant(user, item.brand, request)
    if err:
        return None, err
    return item, None


def get_tenant_ingredient(user, ingredient_id, request=None):
    from restaurant.models import Ingredient
    try:
        ing = Ingredient.objects.select_related('brand').get(id=ingredient_id)
    except Ingredient.DoesNotExist:
        return None, Response({'error': 'Malzeme bulunamadı'}, status=status.HTTP_400_BAD_REQUEST)
    err = deny_cross_tenant(user, ing.brand, request)
    if err:
        return None, err
    return ing, None


def get_tenant_order(user, order_id, request=None):
    from restaurant.models import Order
    try:
        order = Order.objects.select_related('brand').get(id=order_id)
    except Order.DoesNotExist:
        return None, Response({'error': 'Sipariş bulunamadı'}, status=status.HTTP_400_BAD_REQUEST)
    err = deny_cross_tenant(user, order.brand, request)
    if err:
        return None, err
    return order, None


def get_tenant_register(user, register_id, request=None):
    from restaurant.models import CashRegister
    try:
        register = CashRegister.objects.select_related('brand').get(id=register_id)
    except CashRegister.DoesNotExist:
        return None, Response({'error': 'Kasa bulunamadı'}, status=status.HTTP_400_BAD_REQUEST)
    err = deny_cross_tenant(user, register.brand, request)
    if err:
        return None, err
    return register, None
