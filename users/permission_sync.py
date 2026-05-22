from users.models import Permission, Role
from users.permission_catalog import DEFAULT_ROLES, PERMISSIONS


def sync_permissions_to_db(reset_system_role_permissions=False):
    """Katalogdaki izinleri veritabanına yazar; yeni fonksiyon izinlerini ekler."""
    perm_map = {}
    for codename, name, module, kind, sort_order, description in PERMISSIONS:
        perm, _ = Permission.objects.update_or_create(
            codename=codename,
            defaults={
                'name': name,
                'module': module,
                'kind': kind,
                'sort_order': sort_order,
                'description': description,
            },
        )
        perm_map[codename] = perm

    if reset_system_role_permissions:
        for slug, data in DEFAULT_ROLES.items():
            role, _ = Role.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'is_system': data.get('is_system', False),
                },
            )
            role.permissions.set([perm_map[c] for c in data['permissions'] if c in perm_map])

    return perm_map
