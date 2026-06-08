from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from restaurant.tests.helpers import api_url, authenticate_client, create_restaurant_owner


class PlanEnforcementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        expired = timezone.localdate() - timedelta(days=10)
        self.owner, self.brand, self.token = create_restaurant_owner(
            'owner',
            brand_name='Expired Brand',
            plan='starter',
            plan_expiry=expired,
        )
        authenticate_client(self.client, self.token, self.brand)

    def test_expired_brand_blocked_on_write(self):
        res = self.client.post(api_url('categories/'), {'name': 'New Cat', 'icon': 'x'}, format='json')
        self.assertEqual(res.status_code, 402)

    def test_expired_brand_blocked_on_sensitive_read(self):
        res = self.client.get(api_url('report-stats/'))
        self.assertEqual(res.status_code, 402)
