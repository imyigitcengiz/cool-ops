"""Restoran API rol tabanlı izinler."""

from rest_framework.permissions import BasePermission

from restaurant.api.security import ADMIN_ROLES, FINANCE_ROLES, is_api_superuser
from restaurant.compat import get_api_profile


class IsRestaurantFinanceRole(BasePermission):
    """Kasa, gider ve finans kayıtları — store_owner, manager, cashier."""

    def has_permission(self, request, view):
        if is_api_superuser(request.user):
            return True
        profile = get_api_profile(request.user, request)
        return profile.role in FINANCE_ROLES


class IsRestaurantAdminRole(BasePermission):
    """Kullanıcı / şube yönetimi — store_owner, manager."""

    def has_permission(self, request, view):
        if is_api_superuser(request.user):
            return True
        profile = get_api_profile(request.user, request)
        return profile.role in ADMIN_ROLES
