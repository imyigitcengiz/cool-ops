from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_userprofile_business_mode'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='business_mode',
        ),
    ]
