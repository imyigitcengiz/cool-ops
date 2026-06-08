"""Restoran dikeyi abonelik planlarını oluşturur."""

from django.core.management.base import BaseCommand

from core_settings.models import Plan


RESTAURANT_PLANS = (
    {
        'name': 'Restoran Starter',
        'slug': 'restoran-starter',
        'restaurant_plan_tier': 'starter',
        'price': 0,
        'trial_days': 14,
        'billing_days': 30,
        'max_brands': 1,
        'max_users_per_brand': 5,
        'included_module_slugs': ['restaurant', 'settings'],
    },
    {
        'name': 'Restoran Growth',
        'slug': 'restoran-growth',
        'restaurant_plan_tier': 'growth',
        'price': 999,
        'trial_days': 14,
        'billing_days': 30,
        'max_brands': 1,
        'max_users_per_brand': 15,
        'included_module_slugs': ['restaurant', 'settings', 'outreach'],
    },
    {
        'name': 'Restoran Enterprise',
        'slug': 'restoran-enterprise',
        'restaurant_plan_tier': 'enterprise',
        'price': 1999,
        'trial_days': 14,
        'billing_days': 30,
        'max_brands': 3,
        'max_users_per_brand': 999,
        'included_module_slugs': ['restaurant', 'settings', 'outreach', 'contact'],
    },
)


class Command(BaseCommand):
    help = 'Restoran vertical plan kayıtlarını seed eder'

    def handle(self, *args, **options):
        for spec in RESTAURANT_PLANS:
            plan, created = Plan.objects.update_or_create(
                name=spec['name'],
                defaults={
                    'price': spec['price'],
                    'restaurant_plan_tier': spec['restaurant_plan_tier'],
                    'trial_days': spec['trial_days'],
                    'billing_days': spec['billing_days'],
                    'is_active': True,
                    'max_brands': spec['max_brands'],
                    'max_users_per_brand': spec['max_users_per_brand'],
                    'included_module_slugs': spec['included_module_slugs'],
                },
            )
            verb = 'Oluşturuldu' if created else 'Güncellendi'
            self.stdout.write(f'{verb}: {plan.name}')
