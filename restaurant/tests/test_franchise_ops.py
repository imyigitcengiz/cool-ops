from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from restaurant.models import Branch, Category, FranchisePanelToken, MenuItem, Table
from restaurant.tests.helpers import api_url, authenticate_client, create_restaurant_owner


class FranchiseOpsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner, self.brand, self.token = create_restaurant_owner(
            'fr_owner',
            brand_name='Franchise Co',
            plan='growth',
        )
        authenticate_client(self.client, self.token, self.brand)
        self.branch_a = Branch.objects.create(
            brand=self.brand,
            name='Şube A',
            city='İzmir',
            panel_slug='fr-co-sube-a',
            panel_enabled=True,
            is_active=True,
        )
        self.branch_a.panel_password = 'hashed'
        self.branch_b = Branch.objects.create(brand=self.brand, name='Şube B', city='Ankara')
        self.table_a = Table.objects.create(brand=self.brand, branch=self.branch_a, name='A1', capacity=4)
        self.table_b = Table.objects.create(brand=self.brand, branch=self.branch_b, name='B1', capacity=4)
        cat = Category.objects.create(brand=self.brand, name='Ana', icon='utensils')
        self.menu_item = MenuItem.objects.create(brand=self.brand, category=cat, name='Çay', price=15)
        self.token = FranchisePanelToken.objects.create(
            branch=self.branch_a,
            key='test-franchise-token-key',
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.headers = {'HTTP_FRANCHISE_TOKEN': self.token.key}

    def test_create_order_on_own_branch_table(self):
        res = self.client.post(
            api_url('franchise/orders/'),
            {'table': self.table_a.id, 'items': [{'menu_item': self.menu_item.id, 'quantity': 2}]},
            format='json',
            **self.headers,
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(float(res.data['total_amount']), 30.0)
        self.table_a.refresh_from_db()
        self.assertEqual(self.table_a.status, 'occupied')

    def test_cannot_order_on_other_branch_table(self):
        res = self.client.post(
            api_url('franchise/orders/'),
            {'table': self.table_b.id, 'items': [{'menu_item': self.menu_item.id, 'quantity': 1}]},
            format='json',
            **self.headers,
        )
        self.assertEqual(res.status_code, 404)

    def test_change_table_status(self):
        res = self.client.post(
            api_url(f'franchise/tables/{self.table_a.id}/change_status/'),
            {'status': 'bill_requested'},
            format='json',
            **self.headers,
        )
        self.assertEqual(res.status_code, 200)
        self.table_a.refresh_from_db()
        self.assertEqual(self.table_a.status, 'bill_requested')

    def test_menu_endpoint(self):
        res = self.client.get(api_url('franchise/menu/'), **self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['menu_items']), 1)
