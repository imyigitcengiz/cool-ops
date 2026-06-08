from users.permission_catalog import DEFAULT_ROLES, PERMISSIONS


def sync_permissions_to_db(reset_system_role_permissions=False, apps=None):
    """Katalogdaki izinleri veritabanına yazar; yeni fonksiyon izinlerini ekler."""
    if apps is not None:
        Permission = apps.get_model('users', 'Permission')
        Role = apps.get_model('users', 'Role')
    else:
        from users.models import Permission, Role

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
            defaults = {
                'name': data['name'],
                'description': data['description'],
                'is_system': data.get('is_system', False),
            }
            role_field_names = {f.name for f in Role._meta.get_fields()}
            if 'scope' in role_field_names:
                defaults['scope'] = data.get('scope', 'tenant_custom')
            if 'app_id' in role_field_names:
                defaults['app_id'] = data.get('app_id', '')
            role, created = Role.objects.get_or_create(slug=slug, defaults=defaults)
            if not created:
                updates = {}
                if 'scope' in role_field_names and data.get('scope'):
                    updates['scope'] = data['scope']
                if 'app_id' in role_field_names and 'app_id' in data:
                    updates['app_id'] = data['app_id']
                if data.get('is_system'):
                    updates['is_system'] = True
                if updates:
                    for key, value in updates.items():
                        setattr(role, key, value)
                    role.save(update_fields=list(updates.keys()))
            role.permissions.set([perm_map[c] for c in data['permissions'] if c in perm_map])

    return perm_map
