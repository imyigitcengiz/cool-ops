from django.db import migrations, models

from core_settings.color_utils import DEFAULT_HEX, TAILWIND_TO_HEX


def tailwind_to_hex(apps, schema_editor):
    for model_name, kind in (
        ('StatusOption', 'status'),
        ('PriorityOption', 'priority'),
    ):
        Model = apps.get_model('core_settings', model_name)
        fallback = DEFAULT_HEX[kind]
        for obj in Model.objects.all():
            raw = (obj.color or '').strip().lower()
            if raw.startswith('#'):
                continue
            obj.color = TAILWIND_TO_HEX.get(raw, fallback)
            obj.save(update_fields=['color'])


def add_default_colors(apps, schema_editor):
    ProductOption = apps.get_model('core_settings', 'ProductOption')
    ServiceTypeOption = apps.get_model('core_settings', 'ServiceTypeOption')
    for obj in ProductOption.objects.filter(color=''):
        obj.color = DEFAULT_HEX['product']
        obj.save(update_fields=['color'])
    for obj in ServiceTypeOption.objects.filter(color=''):
        obj.color = DEFAULT_HEX['service_type']
        obj.save(update_fields=['color'])


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0006_sitesettings_ai_chat_enabled_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productoption',
            name='color',
            field=models.CharField(default='#0284c7', max_length=7, verbose_name='Renk'),
        ),
        migrations.AddField(
            model_name='servicetypeoption',
            name='color',
            field=models.CharField(default='#8b5cf6', max_length=7, verbose_name='Renk'),
        ),
        migrations.AlterField(
            model_name='priorityoption',
            name='color',
            field=models.CharField(default='#6b7280', max_length=7, verbose_name='Renk'),
        ),
        migrations.AlterField(
            model_name='statusoption',
            name='color',
            field=models.CharField(default='#3b82f6', max_length=7, verbose_name='Renk'),
        ),
        migrations.RunPython(tailwind_to_hex, migrations.RunPython.noop),
        migrations.RunPython(add_default_colors, migrations.RunPython.noop),
    ]
