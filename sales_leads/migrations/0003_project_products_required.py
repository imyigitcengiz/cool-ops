from django.db import migrations, models


def copy_customer_products_to_leads(apps, schema_editor):
    SalesLead = apps.get_model('sales_leads', 'SalesLead')
    for lead in SalesLead.objects.select_related('customer').iterator():
        if not lead.project:
            names = list(lead.customer.products.values_list('name', flat=True))
            lead.project = ', '.join(names) if names else f'Proje #{lead.pk}'
            lead.save(update_fields=['project'])
        product_ids = list(lead.customer.products.values_list('id', flat=True))
        if product_ids:
            lead.products.set(product_ids)


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0001_initial'),
        ('sales_leads', '0002_payment_fields_and_project'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleslead',
            name='products',
            field=models.ManyToManyField(
                blank=True,
                related_name='sales_leads',
                to='core_settings.productoption',
                verbose_name='Proje ürünleri',
            ),
        ),
        migrations.RunPython(copy_customer_products_to_leads, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='saleslead',
            name='project',
            field=models.CharField(max_length=255, verbose_name='Proje'),
        ),
    ]
