from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from restaurant.tests.helpers import api_url, authenticate_client, create_restaurant_owner, create_restaurant_staff
from users.utils import get_or_create_user_profile

User = get_user_model()


class RoleEscalationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner, self.brand, self.token = create_restaurant_owner('owner', brand_name='Brand')
        self.staff, _ = create_restaurant_staff(self.owner, self.brand, 'staff1', restaurant_role='waiter')
        authenticate_client(self.client, self.token, self.brand)

    def test_store_owner_cannot_assign_super_admin(self):
        res = self.client.patch(
            api_url(f'auth/users/{self.staff.id}/'),
            {'role': 'super_admin'},
            format='json',
        )
        self.assertEqual(res.status_code, 403)

    def test_store_owner_can_assign_waiter(self):
        res = self.client.patch(
            api_url(f'auth/users/{self.staff.id}/'),
            {'role': 'kitchen'},
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['user']['role'], 'kitchen')

    def test_fake_super_admin_role_cannot_impersonate(self):
        """DB'de restaurant_role=super_admin olsa bile Django süper kullanıcı değilse yetki yok."""
        impostor = User.objects.create_user(username='fake_super', password='pass12345')
        profile = get_or_create_user_profile(impostor)
        profile.restaurant_role = 'super_admin'
        profile.save()
        token = Token.objects.create(user=impostor)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        res = client.post(api_url(f'auth/users/{self.owner.id}/impersonate/'))
        self.assertEqual(res.status_code, 403)

    def test_fake_super_admin_cannot_access_platform_metrics(self):
        impostor = User.objects.create_user(username='fake_metrics', password='pass12345')
        profile = get_or_create_user_profile(impostor)
        profile.restaurant_role = 'super_admin'
        profile.save()
        token = Token.objects.create(user=impostor)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        res = client.get(api_url('auth/platform-metrics/'))
        self.assertEqual(res.status_code, 403)
