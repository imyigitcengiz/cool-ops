"""Süper admin marka girişi — Marka incele impersonation."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from common.brand_scope import create_brand_for_user
from core_settings.models import SiteSettings
from users.impersonation import SESSION_IMPERSONATE_USER_ID

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
        self.assertEqual(session.get(SESSION_IMPERSONATE_USER_ID), self.owner.pk)

    def test_inspect_stop_returns_to_yonetim(self):
        self.client.force_login(self.superuser)
        self.client.post(reverse('admin_brand_inspect', args=[self.brand.pk]))
        res = self.client.post(reverse('impersonate_stop'))
        self.assertRedirects(res, reverse('admin_dashboard'))
        self.assertNotIn(SESSION_IMPERSONATE_USER_ID, self.client.session)

    def test_impersonate_start_url_removed(self):
        self.client.force_login(self.superuser)
        res = self.client.post(f'/yonetim/kullanicilar/{self.owner.pk}/gecis/')
        self.assertEqual(res.status_code, 404)
