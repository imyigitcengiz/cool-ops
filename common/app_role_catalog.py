"""Uygulama özel rol kataloğu — KobiPOS ve ortak atama kuralları."""

from __future__ import annotations

RESTAURANT_APP_ROLES = (
    {'slug': 'store_owner', 'name': 'Kurum Yöneticisi', 'rank': 100},
    {'slug': 'manager', 'name': 'Operasyon Müdürü', 'rank': 80},
    {'slug': 'waiter', 'name': 'Servis Sorumlusu', 'rank': 50},
    {'slug': 'cashier', 'name': 'Finans Sorumlusu', 'rank': 60},
    {'slug': 'kitchen', 'name': 'Üretim Sorumlusu', 'rank': 40},
)

RESTAURANT_ROLE_SLUGS = frozenset(row['slug'] for row in RESTAURANT_APP_ROLES)

STORE_OWNER_ASSIGNABLE_ROLES = frozenset({'manager', 'waiter', 'cashier', 'kitchen'})
SUPERUSER_ASSIGNABLE_ROLES = frozenset(RESTAURANT_ROLE_SLUGS)


def restaurant_role_label(slug: str) -> str:
    for row in RESTAURANT_APP_ROLES:
        if row['slug'] == slug:
            return row['name']
    return slug or '—'


def restaurant_role_choices(*, include_blank: bool = False, assigner_role: str = 'store_owner', assigner_is_superuser: bool = False):
    allowed = assignable_restaurant_role_slugs(
        assigner_role=assigner_role,
        assigner_is_superuser=assigner_is_superuser,
    )
    choices = [(row['slug'], row['name']) for row in RESTAURANT_APP_ROLES if row['slug'] in allowed]
    if include_blank:
        return [('', '—')] + choices
    return choices


def assignable_restaurant_role_slugs(*, assigner_role: str = 'store_owner', assigner_is_superuser: bool = False) -> frozenset[str]:
    if assigner_is_superuser:
        return SUPERUSER_ASSIGNABLE_ROLES
    if assigner_role == 'store_owner':
        return STORE_OWNER_ASSIGNABLE_ROLES | {'store_owner'}
    if assigner_role == 'manager':
        return STORE_OWNER_ASSIGNABLE_ROLES
    return frozenset()


def validate_restaurant_role_assignment(
    *,
    assigner_is_superuser: bool = False,
    assigner_role: str = '',
    new_role: str,
) -> tuple[bool, str | None]:
    if new_role == 'super_admin':
        return False, 'super_admin rolü atanamaz.'
    if new_role not in RESTAURANT_ROLE_SLUGS:
        return False, f'"{new_role}" geçerli bir KobiPOS rolü değil.'
    allowed = assignable_restaurant_role_slugs(
        assigner_role=assigner_role,
        assigner_is_superuser=assigner_is_superuser,
    )
    if new_role not in allowed:
        return False, f'"{new_role}" rolünü atama yetkiniz yok.'
    return True, None


def assignable_restaurant_roles_for_brand_manager(manager, brand=None) -> list[dict]:
    """Abonelik sahibi panelinden atanabilir KobiPOS rolleri."""
    from common.panel_routing import is_restaurant_brand

    if brand and not is_restaurant_brand(brand):
        return []
    slugs = assignable_restaurant_role_slugs(
        assigner_role='store_owner',
        assigner_is_superuser=bool(manager and manager.is_superuser),
    )
    return [row for row in RESTAURANT_APP_ROLES if row['slug'] in slugs]
