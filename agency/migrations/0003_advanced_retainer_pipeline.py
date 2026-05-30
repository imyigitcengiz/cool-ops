import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0002_import_legacy_analytics_projects'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='agencyclient',
            name='contract_end',
            field=models.DateField(blank=True, null=True, verbose_name='Sözleşme bitiş'),
        ),
        migrations.AddField(
            model_name='agencyclient',
            name='contract_start',
            field=models.DateField(blank=True, null=True, verbose_name='Sözleşme başlangıç'),
        ),
        migrations.AddField(
            model_name='agencyclient',
            name='industry',
            field=models.CharField(blank=True, max_length=120, verbose_name='Sektör'),
        ),
        migrations.AddField(
            model_name='agencyclient',
            name='website',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='agencyproject',
            name='monthly_hours_cap',
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text='Opsiyonel — retainer kapsamındaki max saat.',
                max_digits=8,
                null=True,
                verbose_name='Aylık saat kotası',
            ),
        ),
        migrations.AddField(
            model_name='agencyproject',
            name='revision_rounds_included',
            field=models.PositiveSmallIntegerField(default=2, verbose_name='Dahil revizyon turu'),
        ),
        migrations.AddField(
            model_name='agencyproject',
            name='scope_summary',
            field=models.TextField(
                blank=True,
                help_text='Bu ay teslim edilecek işlerin özeti.',
                verbose_name='Aylık scope özeti',
            ),
        ),
        migrations.AddField(
            model_name='agencydeal',
            name='probability',
            field=models.PositiveSmallIntegerField(
                default=30,
                help_text='0–100',
                verbose_name='Kazanma olasılığı %',
            ),
        ),
        migrations.CreateModel(
            name='AgencyDeliverable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('is_done', models.BooleanField(default=False)),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
                ('notes', models.CharField(blank=True, max_length=500)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deliverables', to='agency.agencyproject')),
            ],
            options={
                'verbose_name': 'Deliverable',
                'verbose_name_plural': 'Deliverablelar',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='AgencyProjectAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_label', models.CharField(blank=True, max_length=120, verbose_name='Rol')),
                ('hours_budget', models.DecimalField(blank=True, decimal_places=1, max_digits=8, null=True, verbose_name='Bütçelenen saat')),
                ('hourly_rate_override', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Özel saat ücreti')),
                ('notes', models.TextField(blank=True)),
                ('freelancer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='agency.agencyfreelancer')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='agency.agencyproject')),
            ],
            options={
                'verbose_name': 'Proje ataması',
                'verbose_name_plural': 'Proje atamaları',
                'ordering': ['freelancer__name'],
                'unique_together': {('project', 'freelancer')},
            },
        ),
        migrations.AddField(
            model_name='agencyproject',
            name='source_deal',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='projects_spawned',
                to='agency.agencydeal',
                verbose_name='Kaynak pipeline',
            ),
        ),
        migrations.AddField(
            model_name='agencydeal',
            name='converted_project',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pipeline_origin',
                to='agency.agencyproject',
            ),
        ),
    ]
