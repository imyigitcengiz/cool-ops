from django.db import migrations, models

PLATFORM_SYSTEM_SLUGS = ('admin',)
APP_PRESET_KOBIOPS_SLUGS = ('operation', 'service', 'sales', 'accounting', 'restaurant_access')


def backfill_role_scope(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    for role in Role.objects.all():
        if role.slug in PLATFORM_SYSTEM_SLUGS:
            role.scope = 'platform_system'
            role.app_id = ''
        elif role.slug in APP_PRESET_KOBIOPS_SLUGS or (
            role.is_system and role.owner_id is None
        ):
            if role.slug not in PLATFORM_SYSTEM_SLUGS:
                role.scope = 'app_preset'
                role.app_id = 'kobiops'
        elif role.owner_id:
            role.scope = 'tenant_custom'
            role.app_id = ''
        else:
            role.scope = 'tenant_custom'
        role.save(update_fields=['scope', 'app_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_restaurant_integration'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='app_id',
            field=models.CharField(
                blank=True,
                choices=[('', '—'), ('kobiops', 'KobiOPS'), ('kobipos', 'KobiPOS')],
                default='',
                max_length=20,
                verbose_name='Uygulama',
            ),
        ),
        migrations.AddField(
            model_name='role',
            name='scope',
            field=models.CharField(
                choices=[
                    ('platform_system', 'Platform sistemi'),
                    ('app_preset', 'Uygulama şablonu'),
                    ('tenant_custom', 'Abonelik özel'),
                ],
                default='tenant_custom',
                max_length=20,
                verbose_name='Kapsam',
            ),
        ),
        migrations.RunPython(backfill_role_scope, migrations.RunPython.noop),
    ]
