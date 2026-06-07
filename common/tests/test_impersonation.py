"""Süper admin marka girişi — impersonate UI kaldırıldı."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from common.brand_scope import create_brand_for_user
from core_settings.models import SiteSettings

User = get_user_model()


class SuperAdminBrandAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        SiteSettings.objects.create(site_name='SA Brand Test')
        self.superuser = User.objects.create_superuser(
            username='superadmin',
            password='test-pass-12345',
        )
        self.owner = User.objects.create_user(username='owner', password='test-pass-12345')
        self.brand = create_brand_for_user(self.owner, 'Test Marka')

    def test_superuser_opens_brand_directly(self):
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_inspect', args=[self.brand.pk]))
        self.assertRedirects(res, '/panel/')
        session = self.client.session
        self.assertEqual(session.get('active_brand_id'), self.brand.pk)

    def test_impersonate_start_url_removed(self):
        self.client.force_login(self.superuser)
        res = self.client.post(f'/yonetim/kullanicilar/{self.owner.pk}/gecis/')
        self.assertEqual(res.status_code, 404)
