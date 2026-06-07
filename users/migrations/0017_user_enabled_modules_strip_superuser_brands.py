from django.db import migrations, models


def strip_superuser_memberships(apps, schema_editor):
    User = apps.get_model('users', 'User')
    BrandMembership = apps.get_model('core_settings', 'BrandMembership')
    super_ids = list(User.objects.filter(is_superuser=True).values_list('pk', flat=True))
    if super_ids:
        BrandMembership.objects.filter(user_id__in=super_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0057_plan_modules_and_panel_limits'),
        ('users', '0016_platform_audit_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='enabled_module_slugs',
            field=models.JSONField(blank=True, default=list, help_text='Abonelik planı tavanı içinde açık modüller.', verbose_name='Aktif modüller'),
        ),
        migrations.RunPython(strip_superuser_memberships, migrations.RunPython.noop),
    ]
