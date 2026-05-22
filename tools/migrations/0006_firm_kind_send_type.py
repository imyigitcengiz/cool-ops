# Generated manually

from django.db import migrations, models
import django.db.models.deletion


def map_send_type(apps, schema_editor):
    WhatsappOutboundMessage = apps.get_model('tools', 'WhatsappOutboundMessage')
    for msg in WhatsappOutboundMessage.objects.all().iterator():
        if msg.send_type:
            continue
        src = msg.source or ''
        if src == 'auto':
            msg.send_type = 'auto'
        elif src == 'scraped':
            msg.send_type = 'scraped_firm'
        elif msg.collection_id:
            msg.send_type = 'campaign'
        else:
            Firm = apps.get_model('tools', 'MapsScrapedFirm')
            if msg.firm_id:
                firm = Firm.objects.filter(pk=msg.firm_id).first()
                if firm and getattr(firm, 'notes', '') == 'Müşteri mesajı':
                    msg.send_type = 'customer'
                elif firm and getattr(firm, 'firm_kind', '') == 'partner':
                    msg.send_type = 'partner'
                else:
                    msg.send_type = 'private'
            else:
                msg.send_type = 'private'
        msg.save(update_fields=['send_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0021_dynamic_payments_product_lines'),
        ('tools', '0005_whatsapp_connection'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapsscrapedfirm',
            name='firm_kind',
            field=models.CharField(
                choices=[
                    ('scraped', 'Kazınan'),
                    ('partner', 'Çözüm ortağı'),
                    ('dealer', 'Bayi'),
                    ('business', 'İş ortağı'),
                ],
                db_index=True,
                default='scraped',
                max_length=20,
                verbose_name='Firma türü',
            ),
        ),
        migrations.AddField(
            model_name='mapsscrapedfirm',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Aktif'),
        ),
        migrations.AddField(
            model_name='mapsscrapedfirm',
            name='solution_partner',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='directory_entry',
                to='core_settings.solutionpartner',
                verbose_name='Çözüm ortağı kaydı',
            ),
        ),
        migrations.AddField(
            model_name='whatsappoutboundmessage',
            name='send_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('customer', 'Müşteri'),
                    ('scraped_firm', 'Kazınan firma'),
                    ('partner', 'Çözüm ortağı'),
                    ('dealer', 'Bayi'),
                    ('business', 'İş ortağı'),
                    ('campaign', 'Kampanya'),
                    ('private', 'Özel (toplu)'),
                    ('auto', 'Otomatik senaryo'),
                ],
                db_index=True,
                default='',
                max_length=24,
                verbose_name='Gönderim türü',
            ),
        ),
        migrations.RunPython(map_send_type, migrations.RunPython.noop),
    ]
