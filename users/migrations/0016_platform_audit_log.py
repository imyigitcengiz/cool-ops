import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0056_brand_tenant_routing'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0015_impersonation_audit'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('brand_inspect', 'Marka inceleme'), ('backup_export', 'Tam yedek indirme'), ('brand_backup_export', 'Marka yedeği indirme'), ('factory_reset', 'Fabrika sıfırlama'), ('brand_delete', 'Marka silme')], max_length=32)),
                ('detail', models.CharField(blank=True, default='', max_length=500)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='platform_audits', to=settings.AUTH_USER_MODEL)),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='platform_audits', to='core_settings.businessbrand')),
                ('target_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='platform_audits_as_target', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Platform denetim kaydı',
                'verbose_name_plural': 'Platform denetim kayıtları',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['-created_at'], name='users_platf_created_6a0f0d_idx'),
                    models.Index(fields=['action', '-created_at'], name='users_platf_action_8c1b2a_idx'),
                ],
            },
        ),
    ]
