"""Marka incele → KobiPOS erişimi ve first_owner."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from common.brand_scope import create_brand_for_user
from core_settings.models import Plan, SiteSettings
from restaurant.compat import ensure_restaurant_tenant, get_tenant_profile
from restaurant.tests.helpers import create_restaurant_owner
from users.impersonation import SESSION_IMPERSONATE_USER_ID

User = get_user_model()


class BrandInspectAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        SiteSettings.objects.create(site_name='Inspect Test')
        self.superuser = User.objects.create_superuser(
            username='superadmin',
            password='test-pass-12345',
        )

    def test_kobiops_brand_inspect_impersonates_owner(self):
        owner = User.objects.create_user(username='kops_owner', password='test-pass-12345')
        brand = create_brand_for_user(owner, 'KobiOPS Marka')
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_inspect', args=[brand.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/panel/')
        self.assertEqual(self.client.session.get(SESSION_IMPERSONATE_USER_ID), owner.pk)
        self.assertEqual(self.client.session.get('active_brand_id'), brand.pk)
        panel_res = self.client.get('/panel/')
        self.assertEqual(panel_res.status_code, 200)

    def test_kobipos_brand_inspect_reaches_spa(self):
        owner, brand, _token = create_restaurant_owner('pos_owner', brand_name='KobiPOS Marka')
        ensure_restaurant_tenant(brand)
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_inspect', args=[brand.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/restoran/')
        self.assertEqual(self.client.session.get(SESSION_IMPERSONATE_USER_ID), owner.pk)
        spa_res = self.client.get('/restoran/dashboard')
        self.assertNotEqual(spa_res.status_code, 500)
        self.assertIn(spa_res.status_code, (200, 302))

    def test_inspect_without_owner_fails(self):
        brand = create_brand_for_user(
            User.objects.create_user(username='orphan', password='test-pass-12345'),
            'Orphan Brand',
        )
        brand.memberships.all().delete()
        brand.first_owner = None
        brand.created_by = None
        brand.save(update_fields=['first_owner', 'created_by'])
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_inspect', args=[brand.pk]))
        self.assertRedirects(res, reverse('admin_brands'))


class FirstOwnerTests(TestCase):
    def test_create_brand_sets_first_owner(self):
        owner = User.objects.create_user(username='founder', password='test-pass-12345')
        brand = create_brand_for_user(owner, 'Founder Brand')
        brand.refresh_from_db()
        self.assertEqual(brand.first_owner_id, owner.pk)
        self.assertEqual(brand.created_by_id, owner.pk)


class PlanSyncTests(TestCase):
    def test_sync_brand_plan_from_owner(self):
        owner, brand, _ = create_restaurant_owner('sync_owner', plan='starter')
        plan = Plan.objects.create(
            name='Growth Restoran',
            restaurant_plan_tier='growth',
            included_module_slugs=['restaurant'],
            is_active=True,
        )
        owner.plan = plan
        owner.save(update_fields=['plan_id'])

        from common.plan_sync import sync_brand_plan_from_owner

        sync_brand_plan_from_owner(owner, brand)
        tenant = get_tenant_profile(brand)
        self.assertEqual(tenant.plan_tier, 'growth')
