from django.db import migrations

KOBI_MODULES = [
    'contact',
    'services',
    'accounting',
    'outreach',
    'integration_data_harvest',
    'integration_whatsapp_bridge',
    'integration_whatsapp_api',
    'integration_media',
]


def normalize_kobi_modules(apps, schema_editor):
    SiteSettings = apps.get_model('core_settings', 'SiteSettings')
    for row in SiteSettings.objects.all():
        row.primary_vertical_slug = 'kobi'
        row.enabled_module_slugs = list(KOBI_MODULES)
        row.save(update_fields=['primary_vertical_slug', 'enabled_module_slugs'])


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0035_strip_capabilities_from_agency'),
    ]

    operations = [
        migrations.RunPython(normalize_kobi_modules, migrations.RunPython.noop),
    ]
