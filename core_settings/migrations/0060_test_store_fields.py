from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core_settings', '0059_plan_trial_billing_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessbrand',
            name='is_test_store',
            field=models.BooleanField(
                default=False,
                help_text='Platform personeli ve süper admin önizlemesi için işaretleyin.',
                verbose_name='Test mağazası',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='default_test_brand_kobiops',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='core_settings.businessbrand',
                verbose_name='Varsayılan KobiOPS test markası',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='default_test_brand_kobipos',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='core_settings.businessbrand',
                verbose_name='Varsayılan KobiPOS test markası',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='test_store_inspectors',
            field=models.ManyToManyField(
                blank=True,
                help_text='Platform yönetim rolündeki kullanıcılar — yalnızca test mağazalarına girebilir.',
                related_name='test_store_inspector_for',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Test mağaza yetkilileri',
            ),
        ),
    ]
