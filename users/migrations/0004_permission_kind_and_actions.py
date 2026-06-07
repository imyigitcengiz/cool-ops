from django.db import migrations, models


def sync_permissions(apps, schema_editor):
    from users.permission_sync import sync_permissions_to_db
    sync_permissions_to_db(reset_system_role_permissions=False, apps=apps)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_rbac_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='permission',
            name='kind',
            field=models.CharField(
                choices=[('access', 'Modül erişimi'), ('action', 'Fonksiyon izni')],
                default='action',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='permission',
            name='description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterModelOptions(
            name='permission',
            options={
                'ordering': ['kind', 'module', 'sort_order', 'name'],
                'verbose_name': 'İzin',
                'verbose_name_plural': 'İzinler',
            },
        ),
        migrations.RunPython(sync_permissions, migrations.RunPython.noop),
    ]
