from django.db import migrations, models

from common.module_plan import default_plan_module_seed


def seed_plan_limits_and_modules(apps, schema_editor):
    Plan = apps.get_model('core_settings', 'Plan')
    defaults = default_plan_module_seed()
    tiers = {
        'Ücretsiz Plan': {'max_hq_brands': 1, 'max_dealer_panels': 0, 'modules': defaults[:4]},
        'Pro Plan': {'max_hq_brands': 1, 'max_dealer_panels': 2, 'modules': defaults},
        'Kurumsal Plan': {'max_hq_brands': 3, 'max_dealer_panels': 10, 'modules': defaults},
    }
    for name, cfg in tiers.items():
        Plan.objects.filter(name=name).update(
            max_hq_brands=cfg['max_hq_brands'],
            max_dealer_panels=cfg['max_dealer_panels'],
            max_brands=cfg['max_hq_brands'] + cfg['max_dealer_panels'],
            included_module_slugs=cfg['modules'],
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0056_brand_tenant_routing'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='max_hq_brands',
            field=models.PositiveIntegerField(default=1, verbose_name='Maksimum merkez panel'),
        ),
        migrations.AddField(
            model_name='plan',
            name='max_dealer_panels',
            field=models.PositiveIntegerField(default=0, verbose_name='Maksimum bayi alt panel'),
        ),
        migrations.AddField(
            model_name='plan',
            name='included_module_slugs',
            field=models.JSONField(blank=True, default=list, verbose_name='Plana dahil modüller'),
        ),
        migrations.AddField(
            model_name='plan',
            name='included_particle_slugs',
            field=models.JSONField(blank=True, default=list, verbose_name='Plana dahil parçacıklar'),
        ),
        migrations.RunPython(seed_plan_limits_and_modules, migrations.RunPython.noop),
    ]
