"""Mevcut kurulumlara yeni finans modüllerini ve parçacıklarını ekle."""

from django.db import migrations

NEW_MODULES = (
    'supplier_payables',
    'e_invoice_bridge',
    'project_costing',
    'multi_cash',
    'projects',
    'timesheet',
)

NEW_PARTICLES = (
    'p.accounting.payables',
    'p.accounting.multi_cash',
    'p.accounting.project_costing',
    'p.accounting.e_export',
    'p.accounting.timesheet',
    'p.accounting.projects',
)


def enable_finance_extensions(apps, schema_editor):
    SiteSettings = apps.get_model('core_settings', 'SiteSettings')
    settings = SiteSettings.objects.first()
    if not settings:
        return
    slugs = list(settings.enabled_module_slugs or [])
    changed = False
    for slug in NEW_MODULES + NEW_PARTICLES:
        if slug not in slugs:
            slugs.append(slug)
            changed = True
    if changed:
        settings.enabled_module_slugs = slugs
        settings.save(update_fields=['enabled_module_slugs'])


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0041_finance_extensions'),
    ]

    operations = [
        migrations.RunPython(enable_finance_extensions, migrations.RunPython.noop),
    ]
