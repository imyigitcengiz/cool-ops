from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales_leads', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleslead',
            name='project',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Proje'),
        ),
        migrations.AddField(
            model_name='saleslead',
            name='down_payment',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Peşinat (₺)'),
        ),
        migrations.AddField(
            model_name='saleslead',
            name='interim_payment_1',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Ara Ödeme (₺)'),
        ),
        migrations.AddField(
            model_name='saleslead',
            name='interim_payment_2',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Ara Ödeme 2 (₺)'),
        ),
        migrations.AlterField(
            model_name='saleslead',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='Not'),
        ),
        migrations.AlterField(
            model_name='saleslead',
            name='sale_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Toplam (₺)'),
        ),
        migrations.AlterField(
            model_name='saleslead',
            name='sale_date',
            field=models.DateField(verbose_name='Tarih'),
        ),
    ]
