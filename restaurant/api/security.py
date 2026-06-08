"""Restoran API güvenlik yardımcıları — platform süper yetkileri yalnızca Django superuser."""

from __future__ import annotations

from django.contrib.auth import get_user_model

User = get_user_model()

# Tenant içi finans / kasa işlemleri
FINANCE_ROLES = frozenset({'store_owner', 'manager', 'cashier'})
# Kullanıcı yönetimi
ADMIN_ROLES = frozenset({'store_owner', 'manager'})


def is_api_superuser(user) -> bool:
    """Platform düzeyi API yetkileri — yalnızca Django is_superuser."""
    return bool(user and getattr(user, 'is_authenticated', False) and user.is_superuser)


def normalize_restaurant_role(stored_role: str, *, user=None) -> str:
    """DB'deki restaurant_role — super_admin yalnızca is_superuser için görüntülenir."""
    if user and is_api_superuser(user):
        return 'super_admin'
    if stored_role == 'super_admin':
        return 'store_owner'
    return stored_role or 'store_owner'


def issue_user_token(user):
    """Impersonate / brand-enter öncesi mevcut token'ı iptal edip yenisini ver."""
    from rest_framework.authtoken.models import Token

    Token.objects.filter(user=user).delete()
    return Token.objects.create(user=user)
