"""Eski tam KOBİ paketini sade çekirdeğe indir; boş listeyi lean preset ile doldur."""

from django.db import migrations


def apply_lean_kobi_defaults(apps, schema_editor):
    from common.kobi_lean_preset import is_legacy_bloated_preset, lean_kobi_slugs

    SiteSettings = apps.get_model('core_settings', 'SiteSettings')
    lean = lean_kobi_slugs()
    for row in SiteSettings.objects.all():
        stored = list(row.enabled_module_slugs or [])
        if not stored or is_legacy_bloated_preset(stored):
            row.enabled_module_slugs = lean
            row.save(update_fields=['enabled_module_slugs'])


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0047_work_schedule_plan'),
    ]

    operations = [
        migrations.RunPython(apply_lean_kobi_defaults, migrations.RunPython.noop),
    ]
