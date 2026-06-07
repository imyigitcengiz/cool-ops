from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0055_fix_plan_limits'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessbrand',
            name='host_slug',
            field=models.SlugField(
                blank=True,
                default='',
                help_text='Boşsa slug kullanılır. Örn. marka.coolops.com için "marka".',
                max_length=80,
                verbose_name='Alan adı kısa adı',
            ),
        ),
        migrations.AddField(
            model_name='businessbrand',
            name='panel_kind',
            field=models.CharField(
                choices=[('hq', 'Merkez panel'), ('dealer', 'Bayi / franchise paneli')],
                default='hq',
                max_length=10,
                verbose_name='Panel türü',
            ),
        ),
        migrations.AddField(
            model_name='businessbrand',
            name='parent_brand',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='dealer_panels',
                to='core_settings.businessbrand',
                verbose_name='Bağlı merkez marka',
            ),
        ),
        migrations.AddField(
            model_name='businessbrand',
            name='tenant_routing',
            field=models.CharField(
                choices=[
                    ('subdomain', 'Alt alan adı (bayi.marka.coolops.com)'),
                    ('path', 'Yol öneki (marka.coolops.com/bayi)'),
                ],
                default='subdomain',
                max_length=12,
                verbose_name='Erişim yapısı',
            ),
        ),
        migrations.AlterField(
            model_name='brandmembership',
            name='role',
            field=models.CharField(
                choices=[
                    ('owner', 'Sahip'),
                    ('member', 'Üye'),
                    ('dealer', 'Bayi kullanıcısı'),
                ],
                default='owner',
                max_length=20,
            ),
        ),
    ]
