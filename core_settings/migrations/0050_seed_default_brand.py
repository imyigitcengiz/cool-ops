"""Site ayarlarından varsayılan marka; mevcut kayıtları ve kullanıcıları bağla."""

from django.conf import settings
from django.db import migrations
from django.utils.text import slugify


def seed_default_brand(apps, schema_editor):
    SiteSettings = apps.get_model('core_settings', 'SiteSettings')
    BusinessBrand = apps.get_model('core_settings', 'BusinessBrand')
    BrandMembership = apps.get_model('core_settings', 'BrandMembership')
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Customer = apps.get_model('customers', 'Customer')
    ServiceRecord = apps.get_model('services', 'ServiceRecord')
    FinanceRecord = apps.get_model('core_settings', 'FinanceRecord')
    SolutionPartner = apps.get_model('core_settings', 'SolutionPartner')
    ServicePersonnel = apps.get_model('core_settings', 'ServicePersonnel')

    site = SiteSettings.objects.order_by('pk').first()
    name = (getattr(site, 'site_name', None) or 'CoolOPS').strip() or 'CoolOPS'
    base_slug = slugify(name) or 'varsayilan'
    slug = base_slug
    n = 1
    while BusinessBrand.objects.filter(slug=slug).exists():
        n += 1
        slug = f'{base_slug}-{n}'

    brand = BusinessBrand.objects.create(
        name=name,
        slug=slug,
        phone=(getattr(site, 'company_phone', None) or '') if site else '',
        address=(getattr(site, 'company_address', None) or '') if site else '',
        currency_code=getattr(site, 'currency_code', 'TRY') if site else 'TRY',
        is_default=True,
        is_active=True,
    )

    for user in User.objects.filter(is_active=True):
        BrandMembership.objects.get_or_create(
            user_id=user.pk,
            brand_id=brand.pk,
            defaults={
                'role': 'owner',
                'is_default': True,
            },
        )

    Customer.objects.filter(brand__isnull=True).update(brand_id=brand.pk)
    ServiceRecord.objects.filter(brand__isnull=True).update(brand_id=brand.pk)
    FinanceRecord.objects.filter(brand__isnull=True).update(brand_id=brand.pk)
    SolutionPartner.objects.filter(brand__isnull=True).update(brand_id=brand.pk)
    ServicePersonnel.objects.filter(brand__isnull=True).update(brand_id=brand.pk)

    for rec in ServiceRecord.objects.filter(brand__isnull=True).exclude(customer__brand__isnull=True):
        rec.brand_id = rec.customer.brand_id
        rec.save(update_fields=['brand_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0049_business_brands'),
        ('customers', '0006_business_brands'),
        ('services', '0016_business_brands'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(seed_default_brand, migrations.RunPython.noop),
    ]
