from django.db import migrations

LEGACY_TO_CAP = {
    'int.whatsapp_bridge': 'cap.whatsapp.send',
    'int.whatsapp_api': 'cap.whatsapp.api',
    'int.media': 'cap.media.library',
    'int.data_harvest': 'cap.data.harvest',
}


def normalize_capability_slugs(apps, schema_editor):
    SiteSettings = apps.get_model('core_settings', 'SiteSettings')
    for row in SiteSettings.objects.all():
        raw = list(row.enabled_module_slugs or [])
        if not raw:
            continue
        out: list[str] = []
        for slug in raw:
            mapped = LEGACY_TO_CAP.get(slug, slug)
            if mapped not in out:
                out.append(mapped)
        if row.primary_vertical_slug in ('kobi', 'agency') and 'cap.data.harvest' not in out:
            if any(s.startswith('cap.') or s.startswith('int.') for s in raw):
                out.append('cap.data.harvest')
        row.enabled_module_slugs = out
        row.save(update_fields=['enabled_module_slugs'])


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0033_refresh_agency_profile_apps'),
    ]

    operations = [
        migrations.RunPython(normalize_capability_slugs, migrations.RunPython.noop),
    ]
