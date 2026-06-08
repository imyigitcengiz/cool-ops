"""Süper admin — marka paneli erişim kuralları."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from common.brand_scope import create_brand_for_user
from core_settings.models import SiteSettings
from users.models import Role

User = get_user_model()


class PlatformAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        SiteSettings.objects.create(site_name='Access Test')
        role = Role.objects.filter(slug='admin').first()
        self.superuser = User.objects.create_superuser(username='super', password='test1234')
        if role:
            self.superuser.role = role
            self.superuser.save()
        self.owner = User.objects.create_user(username='owner', password='test1234')
        if role:
            self.owner.role = role
            self.owner.save()
        create_brand_for_user(self.owner, 'HQ')

    def test_superuser_tenant_panel_redirects_to_yonetim(self):
        self.client.force_login(self.superuser)
        response = self.client.get('/panel/')
        self.assertRedirects(response, '/yonetim/')

    def test_superuser_contact_redirects_to_yonetim(self):
        self.client.force_login(self.superuser)
        response = self.client.get('/contact/')
        self.assertRedirects(response, '/yonetim/')

    def test_superuser_login_panel_next_redirects_to_yonetim(self):
        response = self.client.post('/giris/?next=/panel/', {
            'username': 'super',
            'password': 'test1234',
        }, follow=True)
        self.assertTrue(any(url == '/yonetim/' for url, _ in response.redirect_chain))

    def test_superuser_roles_next_goes_to_roles_page(self):
        response = self.client.post('/giris/?next=/yonetim/roller/', {
            'username': 'super',
            'password': 'test1234',
        })
        self.assertRedirects(response, '/yonetim/roller/')

    def test_owner_can_access_panel(self):
        self.client.force_login(self.owner)
        response = self.client.get('/panel/')
        self.assertEqual(response.status_code, 200)

    def test_settings_backup_redirects_to_super_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.get('/ayarlar/yedekler/')
        self.assertRedirects(response, '/yonetim/yedekler/')

    def test_plain_user_backup_redirects_home(self):
        role = Role.objects.filter(slug='admin').first()
        plain = User.objects.create_user(username='plain', password='test1234', role=role)
        self.client.force_login(plain)
        response = self.client.get('/ayarlar/yedekler/', follow=True)
        self.assertTrue(response.redirect_chain)
        self.assertTrue(response.redirect_chain[-1][0].startswith('/panel/'))

    def test_brand_owner_without_role_can_access_panel(self):
        owner = User.objects.create_user(username='owner_norole', password='test1234')
        create_brand_for_user(owner, 'Norole HQ')
        self.client.force_login(owner)
        response = self.client.get('/panel/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.redirect_chain), 1)

    def test_brand_owner_cannot_access_yonetim(self):
        owner = User.objects.create_user(username='owner_yon', password='test1234')
        create_brand_for_user(owner, 'Yon HQ')
        self.client.force_login(owner)
        response = self.client.get('/yonetim/')
        self.assertEqual(response.status_code, 403)

    def test_staff_without_superuser_cannot_access_django_admin(self):
        staff = User.objects.create_user(username='staff', password='test1234', is_staff=True)
        self.client.force_login(staff)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 403)
