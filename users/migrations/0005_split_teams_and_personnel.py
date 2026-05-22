from django.db import migrations


def grant_teams_to_existing_personnel_roles(apps, schema_editor):
    Permission = apps.get_model('users', 'Permission')
    teams_perm = Permission.objects.filter(codename='contact.teams').first()
    personnel_perm = Permission.objects.filter(codename='contact.personnel').first()
    if not teams_perm or not personnel_perm:
        return
    Role = apps.get_model('users', 'Role')
    for role in Role.objects.filter(permissions=personnel_perm):
        role.permissions.add(teams_perm)


def sync_permissions(apps, schema_editor):
    from users.permission_sync import sync_permissions_to_db
    sync_permissions_to_db(reset_system_role_permissions=False)
    grant_teams_to_existing_personnel_roles(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_permission_kind_and_actions'),
    ]

    operations = [
        migrations.RunPython(sync_permissions, migrations.RunPython.noop),
    ]
