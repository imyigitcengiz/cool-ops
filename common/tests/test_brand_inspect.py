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

    def test_platform_inspector_impersonation_persists_after_get(self):
        from users.models import Role
        from users.permission_catalog import DEFAULT_ROLES
        from users.permission_sync import sync_permissions_to_db

        sync_permissions_to_db()
        admin_data = DEFAULT_ROLES['admin']
        role, _ = Role.objects.get_or_create(
            slug='admin',
            defaults={
                'name': admin_data['name'],
                'description': admin_data['description'],
                'is_system': True,
                'scope': Role.SCOPE_PLATFORM_SYSTEM,
            },
        )
        owner = User.objects.create_user(username='inspector_target', password='test-pass-12345')
        owner.role = role
        owner.save(update_fields=['role_id'])
        test_brand = create_brand_for_user(owner, 'Inspector Persist Brand')
        test_brand.is_test_store = True
        test_brand.save(update_fields=['is_test_store'])

        self.client.force_login(self.inspector)
        self.client.post(reverse('admin_brand_inspect', args=[test_brand.pk]))
        self.assertEqual(self.client.session.get(SESSION_IMPERSONATE_USER_ID), owner.pk)

        panel_res = self.client.get('/panel/')
        self.assertEqual(panel_res.status_code, 200)
        self.assertEqual(self.client.session.get(SESSION_IMPERSONATE_USER_ID), owner.pk)

    def test_logout_clears_impersonation_session(self):
        owner = User.objects.create_user(username='logout_owner', password='test-pass-12345')
        test_brand = create_brand_for_user(owner, 'Logout Test Brand')
        test_brand.is_test_store = True
        test_brand.save(update_fields=['is_test_store'])

        self.client.force_login(self.superuser)
        self.client.post(reverse('admin_brand_inspect', args=[test_brand.pk]))
        self.assertIsNotNone(self.client.session.get(SESSION_IMPERSONATE_USER_ID))

        logout_res = self.client.post(reverse('logout'))
        self.assertEqual(logout_res.status_code, 302)
        self.assertIsNone(self.client.session.get(SESSION_IMPERSONATE_USER_ID))

    def test_impersonate_stop_test_store_redirects_to_panels(self):
        Plan.objects.create(
            name='Restoran Enterprise',
            restaurant_plan_tier='enterprise',
            included_module_slugs=['restaurant'],
            is_active=True,
            price=1999,
        )
        self.client.force_login(self.superuser)
        self.client.post(
            reverse('admin_panel_test_enter'),
            {'panel_id': 'kobipos'},
        )
        stop_res = self.client.post(reverse('impersonate_stop'))
        self.assertRedirects(stop_res, reverse('admin_panels'))
        self.assertIsNone(self.client.session.get(SESSION_IMPERSONATE_USER_ID))

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

    def test_test_store_gets_enterprise_plan_on_inspect(self):
        owner, brand, _ = create_restaurant_owner('low_plan_owner', plan='starter')
        brand.is_test_store = True
        brand.save(update_fields=['is_test_store'])
        starter = Plan.objects.create(
            name='Starter Restoran',
            restaurant_plan_tier='starter',
            included_module_slugs=['restaurant'],
            is_active=True,
        )
        owner.plan = starter
        owner.save(update_fields=['plan_id'])

        self.client.force_login(self.superuser)
        self.client.post(reverse('admin_brand_inspect', args=[brand.pk]))
        owner.refresh_from_db()
        tenant = get_tenant_profile(brand)
        tenant.refresh_from_db()

        self.assertTrue(owner.has_perm_codename('access.restaurant'))
        self.assertEqual(tenant.plan_tier, 'enterprise')
        spa_res = self.client.get('/restoran/dashboard')
        self.assertIn(spa_res.status_code, (200, 302))

    def test_kobiops_test_enter_after_kobipos_uses_kurumsal_plan(self):
        from common.panel_routing import is_restaurant_plan, resolve_brand_panel_id
        from common.platform_test_access import demo_owner_username

        Plan.objects.create(
            name='Restoran Enterprise',
            restaurant_plan_tier='enterprise',
            included_module_slugs=['restaurant'],
            is_active=True,
            price=1999,
        )
        Plan.objects.create(
            name='Kurumsal Plan',
            included_module_slugs=['services', 'contact', 'accounting', 'settings'],
            is_active=True,
            price=2999,
        )
        self.client.force_login(self.superuser)
        self.client.post(
            reverse('admin_panel_test_enter'),
            {'panel_id': 'kobipos'},
        )
        res = self.client.post(
            reverse('admin_panel_test_enter'),
            {'panel_id': 'kobiops'},
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/panel/')
        kops_owner = User.objects.get(username=demo_owner_username('kobiops'))
        self.assertFalse(is_restaurant_plan(kops_owner.plan))
        settings = SiteSettings.objects.get(pk=1)
        self.assertEqual(
            resolve_brand_panel_id(settings.default_test_brand_kobiops, owner=kops_owner),
            'kobiops',
        )
        panel_res = self.client.get('/panel/')
        self.assertEqual(panel_res.status_code, 200)

    def test_panel_test_enter_switches_from_kobiops_to_kobipos(self):
        Plan.objects.create(
            name='Restoran Enterprise',
            restaurant_plan_tier='enterprise',
            included_module_slugs=['restaurant'],
            is_active=True,
            price=1999,
        )
        self.client.force_login(self.superuser)
        first = self.client.post(
            reverse('admin_panel_test_enter'),
            {'panel_id': 'kobiops'},
        )
        self.assertEqual(first.status_code, 302)
        self.assertEqual(first.url, '/panel/')

        second = self.client.post(
            reverse('admin_panel_test_enter'),
            {'panel_id': 'kobipos'},
        )
        self.assertEqual(second.status_code, 302)
        self.assertEqual(second.url, '/restoran/')
        owner = User.objects.select_related('role').get(
            pk=self.client.session.get(SESSION_IMPERSONATE_USER_ID),
        )
        self.assertTrue(owner.has_perm_codename('access.restaurant'))
        spa_res = self.client.get('/restoran/dashboard')
        self.assertIn(spa_res.status_code, (200, 302))

    def test_kobipos_test_enter_auto_creates_enterprise_demo(self):
        Plan.objects.create(
            name='Restoran Enterprise',
            restaurant_plan_tier='enterprise',
            included_module_slugs=['restaurant'],
            is_active=True,
            price=1999,
        )
        self.client.force_login(self.superuser)
        res = self.client.post(
            reverse('admin_panel_test_enter'),
            {'panel_id': 'kobipos'},
        )
        self.assertEqual(res.status_code, 302)
        settings = SiteSettings.objects.get(pk=1)
        brand = settings.default_test_brand_kobipos
        self.assertIsNotNone(brand)
        tenant = get_tenant_profile(brand)
        self.assertEqual(tenant.plan_tier, 'enterprise')
        owner = brand.first_owner
        self.assertTrue(owner.has_perm_codename('access.restaurant'))

    def test_panels_page_shows_close_when_test_session_active(self):
        Plan.objects.create(
            name='Restoran Enterprise',
            restaurant_plan_tier='enterprise',
            included_module_slugs=['restaurant'],
            is_active=True,
            price=1999,
        )
        self.client.force_login(self.superuser)
        self.client.post(
            reverse('admin_panel_test_enter'),
            {'panel_id': 'kobipos'},
        )
        res = self.client.get(reverse('admin_panels'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Açık test marka oturumu')
        self.assertContains(res, 'Test marka oturumu kapat')
        self.assertContains(res, 'Test markaya gir')

        stop_res = self.client.post(reverse('admin_panel_test_stop'))
        self.assertRedirects(stop_res, reverse('admin_panels'))
        self.assertIsNone(self.client.session.get(SESSION_IMPERSONATE_USER_ID))

        cleared = self.client.get(reverse('admin_panels'))
        self.assertNotContains(cleared, 'Açık test marka oturumu')
        self.assertContains(cleared, 'Test markaya gir')

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
        self.assertContains(res, 'Test markaya gir')
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

    def test_test_store_sync_ignores_owner_starter_tier(self):
        from common.plan_sync import (
            TEST_STORE_RESTAURANT_TIER,
            apply_test_store_premium_plan,
            sync_brand_plan_from_owner,
        )

        owner, brand, _ = create_restaurant_owner('test_sync_owner', plan='starter')
        brand.is_test_store = True
        brand.save(update_fields=['is_test_store'])
        apply_test_store_premium_plan(brand, owner=owner)
        owner.plan = Plan.objects.create(
            name='Starter Again',
            restaurant_plan_tier='starter',
            included_module_slugs=['restaurant'],
            is_active=True,
        )
        owner.save(update_fields=['plan_id'])
        sync_brand_plan_from_owner(owner, brand)
        tenant = get_tenant_profile(brand)
        self.assertEqual(tenant.plan_tier, TEST_STORE_RESTAURANT_TIER)
