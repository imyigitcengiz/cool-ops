from django.db import migrations

CAP_PREFIXES = ('cap.', 'int.')


def strip_agency_capabilities(apps, schema_editor):
    SiteSettings = apps.get_model('core_settings', 'SiteSettings')
    for row in SiteSettings.objects.filter(primary_vertical_slug='agency'):
        slugs = list(row.enabled_module_slugs or [])
        cleaned = [s for s in slugs if not s.startswith(CAP_PREFIXES)]
        if cleaned != slugs:
            row.enabled_module_slugs = cleaned
            row.save(update_fields=['enabled_module_slugs'])


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0034_normalize_capability_slugs'),
    ]

    operations = [
        migrations.RunPython(strip_agency_capabilities, migrations.RunPython.noop),
    ]
