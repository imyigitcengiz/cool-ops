from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0013_servicehistory_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicerecord',
            name='list_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name='Normal fiyat',
            ),
        ),
        migrations.AddField(
            model_name='servicerecord',
            name='discounted_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name='İndirimli fiyat',
            ),
        ),
    ]
