from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from common.brand_scope import create_brand_for_user
from core_settings.models import BusinessBrand
from restaurant.compat import ensure_restaurant_tenant
from restaurant.models import RestaurantCategory, RestaurantTable
from users.models import Role
from users.utils import get_or_create_user_profile

User = get_user_model()


class RestaurantTenantIsolationTests(TestCase):
    def setUp(self):
        admin_role, _ = Role.objects.get_or_create(slug='admin', defaults={'name': 'Admin', 'is_system': True})
        self.user_a = User.objects.create_user(username='owner_a', password='pass12345')
        self.user_a.role = admin_role
        self.user_a.enabled_module_slugs = ['restaurant', 'settings']
        self.user_a.save()
        self.user_b = User.objects.create_user(username='owner_b', password='pass12345')
        self.user_b.role = admin_role
        self.user_b.enabled_module_slugs = ['restaurant', 'settings']
        self.user_b.save()
        self.brand_a = create_brand_for_user(self.user_a, 'Restoran A')
        self.brand_b = create_brand_for_user(self.user_b, 'Restoran B')
        ensure_restaurant_tenant(self.brand_a)
        ensure_restaurant_tenant(self.brand_b)
        profile_a = get_or_create_user_profile(self.user_a)
        profile_a.restaurant_role = 'store_owner'
        profile_a.restaurant_brand = self.brand_a
        profile_a.save()
        profile_b = get_or_create_user_profile(self.user_b)
        profile_b.restaurant_role = 'store_owner'
        profile_b.restaurant_brand = self.brand_b
        profile_b.save()
        RestaurantCategory.objects.create(brand=self.brand_a, name='Ana Yemek')
        RestaurantCategory.objects.create(brand=self.brand_b, name='Tatlı')
        self.token_a = Token.objects.create(user=self.user_a)
        self.client = APIClient()

    def test_categories_scoped_per_brand(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        session = self.client.session
        session['active_brand_id'] = self.brand_a.pk
        session.save()
        res = self.client.get('/restoran/api/categories/')
        self.assertEqual(res.status_code, 200)
        names = {row['name'] for row in res.json()}
        self.assertEqual(names, {'Ana Yemek'})
