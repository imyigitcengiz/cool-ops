# Generated manually

from django.db import migrations, models


def copy_trigger_value_to_to(apps, schema_editor):
    WhatsAppTemplate = apps.get_model('core_settings', 'WhatsAppTemplate')
    for row in WhatsAppTemplate.objects.all():
        legacy = (row.trigger_value or '').strip()
        if legacy and not (row.trigger_to or '').strip():
            row.trigger_to = legacy
            row.save(update_fields=['trigger_to'])


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0019_whatsapptemplate_scenarios'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsapptemplate',
            name='trigger_from',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Durum değişiminde önceki değer. Boş = herhangi.',
                max_length=80,
                verbose_name='Eski durum (önce)',
            ),
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='trigger_to',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Oluşturma anındaki durum veya değişim sonrası durum. Boş = herhangi.',
                max_length=80,
                verbose_name='Yeni durum (sonra)',
            ),
        ),
        migrations.RunPython(copy_trigger_value_to_to, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='whatsapptemplate',
            name='trigger_value',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Kullanımdan kalktı — trigger_to kullanın.',
                max_length=80,
                verbose_name='Durum / koşul (eski)',
            ),
        ),
    ]
