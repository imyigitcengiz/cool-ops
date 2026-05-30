from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0028_sitesettings_registration_enabled'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sitesettings',
            name='registration_enabled',
        ),
    ]
