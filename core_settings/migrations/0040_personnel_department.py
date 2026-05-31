from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0039_material_recipe_stock'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonnelDepartment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True, verbose_name='Departman adı')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktif')),
            ],
            options={
                'verbose_name': 'Personel departmanı',
                'verbose_name_plural': 'Personel departmanları',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='servicepersonnel',
            name='department',
            field=models.ForeignKey(
                blank=True,
                help_text='Organizasyon birimi — ofis, tasarım, saha vb.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='personnel',
                to='core_settings.personneldepartment',
                verbose_name='Departman',
            ),
        ),
        migrations.AddField(
            model_name='servicepersonnel',
            name='job_title',
            field=models.CharField(
                blank=True,
                help_text='Örn: Grafik Tasarımcı, Montaj Ustası',
                max_length=120,
                verbose_name='Ünvan',
            ),
        ),
        migrations.AlterField(
            model_name='servicepersonnel',
            name='team',
            field=models.ForeignKey(
                blank=True,
                help_text='Saha servis ekibi — ofis personeli için boş bırakılabilir.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='personnel',
                to='core_settings.serviceteam',
                verbose_name='Ekip',
            ),
        ),
        migrations.AlterModelOptions(
            name='servicepersonnel',
            options={'ordering': ['name'], 'verbose_name': 'Personel', 'verbose_name_plural': 'Personeller'},
        ),
    ]
