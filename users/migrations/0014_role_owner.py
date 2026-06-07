from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_user_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='owner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='owned_roles',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Oluşturan abonelik sahibi',
            ),
        ),
    ]
