from django.db import migrations


def fix_plan_limits(apps, schema_editor):
    Plan = apps.get_model('core_settings', 'Plan')
    Plan.objects.filter(name='Enterprise Plan').update(
        name='Kurumsal Plan',
        max_brands=10,
        max_users_per_brand=25,
        max_customers_per_brand=5000,
    )
    Plan.objects.filter(
        name='Kurumsal Plan',
        max_brands__gte=100,
    ).update(
        max_brands=10,
        max_users_per_brand=25,
        max_customers_per_brand=5000,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0054_billinginvoice'),
    ]

    operations = [
        migrations.RunPython(fix_plan_limits, migrations.RunPython.noop),
    ]
