from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0007_option_colors_hex'),
    ]

    operations = [
        migrations.AddField(
            model_name='productoption',
            name='service_types',
            field=models.ManyToManyField(
                blank=True,
                related_name='products',
                to='core_settings.servicetypeoption',
                verbose_name='İzin verilen arıza / servis tipleri',
            ),
        ),
    ]
