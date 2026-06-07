"""Plan limitleri — müşteri sayısı."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from common.brand_scope import SESSION_ACTIVE_BRAND, create_brand_for_user
from core_settings.models import Plan, SiteSettings
from customers.models import Customer
from users.models import Permission, Role

User = get_user_model()


class CustomerLimitTests(TestCase):
    def setUp(self):
        self.client = Client()
        SiteSettings.objects.create(site_name='Limit Test')
        self.plan = Plan.objects.create(
            name='Mini Plan',
            price=0,
            max_brands=1,
            max_users_per_brand=3,
            max_customers_per_brand=2,
            is_active=True,
        )
        role = Role.objects.create(slug='crm-limit', name='CRM', is_system=False)
        perm, _ = Permission.objects.get_or_create(
            codename='contact.customers',
            defaults={'name': 'Customers', 'module': 'Test', 'kind': 'action', 'sort_order': 0},
        )
        view_perm, _ = Permission.objects.get_or_create(
            codename='contact.customers_view',
            defaults={'name': 'View', 'module': 'Test', 'kind': 'access', 'sort_order': 0},
        )
        access, _ = Permission.objects.get_or_create(
            codename='access.contact',
            defaults={'name': 'Access', 'module': 'Test', 'kind': 'access', 'sort_order': 0},
        )
        role.permissions.add(perm, view_perm, access)

        self.owner = User.objects.create_user(username='limit_owner', password='test1234', role=role)
        self.owner.plan = self.plan
        self.owner.save(update_fields=['plan_id'])
        self.brand = create_brand_for_user(self.owner, 'Limit Marka')
        Customer.objects.create(name='M1', brand=self.brand)
        Customer.objects.create(name='M2', brand=self.brand)

    def _login(self):
        self.client.force_login(self.owner)
        session = self.client.session
        session[SESSION_ACTIVE_BRAND] = self.brand.pk
        session.save()

    def test_customer_create_blocked_at_limit(self):
        self._login()
        response = self.client.post('/contact/musteriler/yeni/', {
            'name': 'M3',
            'phone': '',
            'region': '',
            'address': '',
            'location_link': '',
            'contract_date': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.filter(name='M3').exists())
        self.assertContains(response, 'müşteri limitine')
