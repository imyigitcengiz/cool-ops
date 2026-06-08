from django.test import TestCase
from rest_framework.test import APIClient

from restaurant.models import Branch, Table
from restaurant.tests.helpers import api_url, authenticate_client, create_restaurant_owner


class BranchScopeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner, self.brand, self.token = create_restaurant_owner(
            'branch_owner',
            plan='growth',
            brand_name='Multi Branch',
        )
        authenticate_client(self.client, self.token, self.brand)
        self.branch_a = Branch.objects.create(brand=self.brand, name='Şube A', city='İstanbul')
        self.branch_b = Branch.objects.create(brand=self.brand, name='Şube B', city='Ankara')
        Table.objects.create(brand=self.brand, branch=self.branch_a, name='A1', capacity=4)
        Table.objects.create(brand=self.brand, branch=self.branch_b, name='B1', capacity=4)

    def test_tables_filtered_by_branch_id(self):
        res_all = self.client.get(api_url('tables/'))
        self.assertEqual(res_all.status_code, 200)
        self.assertEqual(len(res_all.data), 2)

        res_a = self.client.get(api_url(f'tables/?branch_id={self.branch_a.id}'))
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(len(res_a.data), 1)
        self.assertEqual(res_a.data[0]['name'], 'A1')
