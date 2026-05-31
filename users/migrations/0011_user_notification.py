from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_fix_rbac_test_user_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField(blank=True)),
                ('link', models.CharField(blank=True, max_length=500)),
                ('level', models.CharField(choices=[('info', 'Bilgi'), ('success', 'Başarılı'), ('warning', 'Uyarı')], default='info', max_length=20)),
                ('source', models.CharField(choices=[('system', 'Sistem'), ('payroll', 'Maaş'), ('receivables', 'Alacak'), ('service', 'Servis')], default='system', max_length=30)),
                ('dedupe_key', models.CharField(blank=True, db_index=True, max_length=120)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='users.user')),
            ],
            options={
                'verbose_name': 'Bildirim',
                'verbose_name_plural': 'Bildirimler',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', 'is_read', '-created_at'], name='users_usern_user_id_8f0b0d_idx')],
            },
        ),
    ]
