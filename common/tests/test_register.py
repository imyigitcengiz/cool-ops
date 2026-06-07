"""Üyelik (kayıt) akışı testleri."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from core_settings.models import BusinessBrand, Plan, SiteSettings

User = get_user_model()


class RegisterViewTests(TestCase):
    def setUp(self):
        SiteSettings.objects.create(site_name='Register Test')
        Plan.objects.get_or_create(
            name='Ücretsiz Plan',
            defaults={'price': 0, 'max_brands': 1, 'is_active': True},
        )
        self.client = Client()

    def test_register_page_public(self):
        response = self.client.get('/kayit/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Üye olun')

    def test_register_creates_user_brand_and_logs_in(self):
        response = self.client.post('/kayit/', {
            'username': 'newbiz',
            'first_name': 'Ali',
            'last_name': 'Veli',
            'email': 'ali@ornek.com',
            'brand_name': 'Yeni İşletme',
            'password1': 'GucluSifre123',
            'password2': 'GucluSifre123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newbiz').exists())
        self.assertTrue(BusinessBrand.objects.filter(name='Yeni İşletme').exists())

    def test_register_rate_limit_blocks_excessive_attempts(self):
        from django.core.cache import cache

        cache.clear()
        payload = {
            'username': 'blocked',
            'first_name': 'A',
            'last_name': 'B',
            'email': 'a@b.com',
            'brand_name': 'X',
            'password1': 'short',
            'password2': 'short',
        }
        for i in range(6):
            self.client.post('/kayit/', {**payload, 'username': f'user{i}'})
        response = self.client.post('/kayit/', {**payload, 'username': 'user6'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='user6').exists())
