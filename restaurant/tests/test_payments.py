from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from restaurant.api.payment_service import get_active_provider
from restaurant.models import Invoice
from restaurant.tests.helpers import api_url, authenticate_client, create_restaurant_owner


class PaymentSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner_a, self.brand_a, self.token_a = create_restaurant_owner('pay_a', brand_name='Pay A')
        self.owner_b, self.brand_b, _ = create_restaurant_owner('pay_b', brand_name='Pay B')
        authenticate_client(self.client, self.token_a, self.brand_a)
        self.invoice_b = Invoice.objects.create(
            brand=self.brand_b,
            invoice_number='INV-TEST-1',
            amount=499,
            plan='growth',
            paid=False,
            payment_status='pending',
        )

    @override_settings(DEBUG=False)
    def test_mock_disabled_in_production(self):
        with self.assertRaises(RuntimeError):
            get_active_provider()

    def test_checkout_requires_own_brand(self):
        res = self.client.post(
            api_url(f'auth/brands/{self.brand_b.id}/checkout/'),
            {'plan': 'growth'},
            format='json',
        )
        self.assertEqual(res.status_code, 403)
