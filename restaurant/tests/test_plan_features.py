from django.test import TestCase
from rest_framework.test import APIClient

from restaurant.tests.helpers import api_url, authenticate_client, create_restaurant_owner


class PlanFeatureGateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner, self.brand, self.token = create_restaurant_owner(
            'feat_owner',
            brand_name='Starter Brand',
            plan='starter',
        )
        authenticate_client(self.client, self.token, self.brand)

    def test_crm_blocked_on_starter(self):
        res = self.client.get(api_url('customers/'))
        self.assertEqual(res.status_code, 403)
