# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0005_whatsapp_connection'),
        ('core_settings', '0018_sitesettings_whatsapp_defaults'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsapptemplate',
            name='auto_send',
            field=models.BooleanField(default=True, verbose_name='Otomatik gönder'),
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='connection',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='scenario_templates',
                to='tools.whatsappconnection',
                verbose_name='Gönderen hat',
            ),
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Aktif'),
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='scenario',
            field=models.CharField(
                choices=[
                    ('service_created', 'Servis kaydı oluşturuldu'),
                    ('service_status', 'Servis durumu değişti'),
                    ('sales_lead_created', 'Satış kaydı oluşturuldu'),
                    ('sales_lead_status', 'Satış durumu değişti'),
                    ('customer_created', 'Müşteri oluşturuldu'),
                ],
                default='service_status',
                max_length=40,
                verbose_name='Senaryo',
            ),
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='sort_order',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='trigger_value',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Boş bırakılırsa senaryodaki tüm durumlar için geçerli olur.',
                max_length=80,
                verbose_name='Durum / koşul',
            ),
        ),
        migrations.AlterField(
            model_name='whatsapptemplate',
            name='message',
            field=models.TextField(verbose_name='Mesaj içeriği'),
        ),
        migrations.AlterField(
            model_name='whatsapptemplate',
            name='title',
            field=models.CharField(max_length=100, verbose_name='Kural adı'),
        ),
        migrations.AlterModelOptions(
            name='whatsapptemplate',
            options={
                'ordering': ['sort_order', 'title'],
                'verbose_name': 'WhatsApp Şablonu',
                'verbose_name_plural': 'WhatsApp Şablonları',
            },
        ),
    ]
