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


class PlatformTestStoreInspectTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.site_settings, _ = SiteSettings.objects.get_or_create(
            pk=1,
            defaults={'site_name': 'Test Store Inspect'},
        )
        self.superuser = User.objects.create_superuser(
            username='superadmin2',
            password='test-pass-12345',
        )
        from users.models import Role

        self.platform_role = Role.objects.create(
            name='Platform Yönetim',
            slug='platform-mgmt-test',
            scope=Role.SCOPE_PLATFORM_SYSTEM,
        )
        self.inspector = User.objects.create_user(
            username='platform_inspector',
            password='test-pass-12345',
            role=self.platform_role,
        )
        self.site_settings.test_store_inspectors.add(self.inspector)

    def test_platform_staff_can_inspect_test_store_only(self):
        owner = User.objects.create_user(username='test_owner', password='test-pass-12345')
        test_brand = create_brand_for_user(owner, 'Test KobiOPS')
        test_brand.is_test_store = True
        test_brand.save(update_fields=['is_test_store'])
        normal_brand = create_brand_for_user(
            User.objects.create_user(username='normal_owner', password='test-pass-12345'),
            'Normal Brand',
        )

        self.client.force_login(self.inspector)
        ok_res = self.client.post(reverse('admin_brand_inspect', args=[test_brand.pk]))
        self.assertEqual(ok_res.status_code, 302)
        self.assertEqual(self.client.session.get(SESSION_IMPERSONATE_USER_ID), owner.pk)

        self.client.logout()
        self.client.force_login(self.inspector)
        deny_res = self.client.post(reverse('admin_brand_inspect', args=[normal_brand.pk]))
        self.assertRedirects(deny_res, reverse('admin_panels'))

    def test_panel_test_enter_auto_creates_demo_brand(self):
        self.client.force_login(self.superuser)
        res = self.client.post(
            reverse('admin_panel_test_enter'),
            {'panel_id': 'kobiops'},
        )
        self.assertEqual(res.status_code, 302)
        from core_settings.models import BusinessBrand, SiteSettings

        settings = SiteSettings.objects.get(pk=1)
        self.assertIsNotNone(settings.default_test_brand_kobiops_id)
        brand = BusinessBrand.objects.get(pk=settings.default_test_brand_kobiops_id)
        self.assertTrue(brand.is_test_store)
        self.assertEqual(self.client.session.get(SESSION_IMPERSONATE_USER_ID), brand.first_owner_id)

    def test_panels_page_shows_test_inspect_not_direct_panel(self):
        owner = User.objects.create_user(username='panel_test_owner', password='test-pass-12345')
        brand = create_brand_for_user(owner, 'Panel Test Brand')
        brand.is_test_store = True
        brand.save(update_fields=['is_test_store'])
        self.site_settings.default_test_brand_kobiops = brand
        self.site_settings.save(update_fields=['default_test_brand_kobiops'])

        self.client.force_login(self.superuser)
        res = self.client.get(reverse('admin_panels'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Test mağazaya gir')
        self.assertNotContains(res, 'Panele git')


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

    def test_ensure_restaurant_tenant_uses_plan_trial_days(self):
        from common.brand_scope import create_brand_for_user

        owner = User.objects.create_user(username='trial_owner', password='test-pass-12345')
        plan = Plan.objects.create(
            name='Uzun Deneme',
            restaurant_plan_tier='starter',
            trial_days=21,
            included_module_slugs=['restaurant'],
            is_active=True,
        )
        owner.plan = plan
        owner.save(update_fields=['plan_id'])
        brand = create_brand_for_user(owner, 'Trial Brand', bypass_plan_limit=True)

        from restaurant.compat import ensure_restaurant_tenant

        ensure_restaurant_tenant(brand, owner=owner)
        tenant = get_tenant_profile(brand)
        from django.utils import timezone
        from datetime import timedelta

        expected = timezone.localdate() + timedelta(days=21)
        self.assertEqual(tenant.plan_expiry, expected)

    def test_billing_days_from_plan_on_upgrade(self):
        from datetime import timedelta

        from django.utils import timezone

        from common.plan_sync import plan_billing_days, sync_owner_brands_from_plan

        owner, brand, _ = create_restaurant_owner('billing_owner', plan='starter')
        plan = Plan.objects.create(
            name='Growth Billing',
            restaurant_plan_tier='growth',
            billing_days=45,
            included_module_slugs=['restaurant'],
            is_active=True,
        )
        owner.plan = plan
        owner.save(update_fields=['plan_id'])
        ensure_restaurant_tenant(brand, owner=owner)
        tenant = get_tenant_profile(brand)
        tenant.plan_expiry = timezone.localdate() + timedelta(days=10)
        tenant.save(update_fields=['plan_expiry'])

        sync_owner_brands_from_plan(owner)
        tenant.refresh_from_db()
        self.assertEqual(tenant.plan_tier, 'growth')
        self.assertEqual(
            tenant.plan_expiry,
            timezone.localdate() + timedelta(days=10 + plan_billing_days(plan)),
        )
