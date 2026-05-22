from django.db import migrations


def sync_customer_view_permissions(apps, schema_editor):
    from users.permission_sync import sync_permissions_to_db

    sync_permissions_to_db(reset_system_role_permissions=True)

    Permission = apps.get_model('users', 'Permission')
    Role = apps.get_model('users', 'Role')

    edit_perm = Permission.objects.filter(codename='contact.customers').first()
    view_perm = Permission.objects.filter(codename='contact.customers_view').first()
    if edit_perm and view_perm:
        for role in Role.objects.filter(permissions=edit_perm):
            role.permissions.add(view_perm)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_split_teams_and_personnel'),
    ]

    operations = [
        migrations.RunPython(sync_customer_view_permissions, migrations.RunPython.noop),
    ]
