from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_agencyproject'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AgencyProject',
        ),
    ]
