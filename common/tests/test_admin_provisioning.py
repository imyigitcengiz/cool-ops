"""Süper admin — kullanıcı ve marka oluşturma."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from core_settings.models import BusinessBrand, BrandMembership, Plan, SiteSettings, BillingInvoice
from users.models import Role, PlatformAuditLog

User = get_user_model()


class SuperAdminProvisioningTests(TestCase):
    def setUp(self):
        self.client = Client()
        SiteSettings.objects.create(site_name='Provision Test')
        Plan.objects.get_or_create(
            name='Ücretsiz Plan',
            defaults={
                'price': 0,
                'max_brands': 1,
                'max_users_per_brand': 5,
                'max_customers_per_brand': 100,
                'is_active': True,
            },
        )
        self.superuser = User.objects.create_superuser(username='super', password='test1234')

    def test_superuser_creates_subscription_owner_with_brand(self):
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_user_create'), {
            'account_type': 'owner',
            'username': 'tenant1',
            'first_name': 'Ali',
            'last_name': 'Veli',
            'email': 'ali@test.com',
            'brand_name': 'Ali Mağaza',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'is_active': 'on',
        })
        self.assertRedirects(res, reverse('admin_users'))
        user = User.objects.get(username='tenant1')
        self.assertFalse(user.is_superuser)
        brand = BusinessBrand.objects.get(name='Ali Mağaza')
        self.assertTrue(
            BrandMembership.objects.filter(
                user=user,
                brand=brand,
                role=BrandMembership.ROLE_OWNER,
            ).exists()
        )

    def test_superuser_creates_brand_for_existing_owner(self):
        owner = User.objects.create_user(username='owner2', password='x')
        BrandMembership.objects.create(
            user=owner,
            brand=BusinessBrand.objects.create(name='Mevcut', slug='mevcut'),
            role=BrandMembership.ROLE_OWNER,
        )
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_create'), {
            'owner': owner.pk,
            'name': 'İkinci Mağaza',
            'panel_kind': BusinessBrand.PANEL_HQ,
            'tenant_routing': BusinessBrand.TENANT_SUBDOMAIN,
        })
        self.assertRedirects(res, reverse('admin_brands'))
        self.assertTrue(BusinessBrand.objects.filter(name='İkinci Mağaza').exists())

    def test_superuser_creates_brand_member_user(self):
        brand = BusinessBrand.objects.create(name='Hedef Marka', slug='hedef-marka')
        staff_role = Role.objects.create(slug='staff', name='Personel', is_system=True)
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_user_create'), {
            'account_type': 'member',
            'username': 'staff1',
            'first_name': 'Ayşe',
            'last_name': 'Kara',
            'email': 'ayse@test.com',
            'brand': brand.pk,
            'role': staff_role.pk,
            'membership_role': BrandMembership.ROLE_MEMBER,
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'is_active': 'on',
        })
        self.assertRedirects(res, reverse('admin_users'))
        user = User.objects.get(username='staff1')
        self.assertTrue(
            BrandMembership.objects.filter(
                user=user,
                brand=brand,
                role=BrandMembership.ROLE_MEMBER,
            ).exists()
        )
        self.assertEqual(user.role_id, staff_role.pk)

    def test_superuser_edits_user_memberships(self):
        brand = BusinessBrand.objects.create(name='Edit Marka', slug='edit-marka')
        user = User.objects.create_user(username='editme', password='x')
        BrandMembership.objects.create(user=user, brand=brand, role=BrandMembership.ROLE_MEMBER)
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_user_edit', kwargs={'pk': user.pk}), {
            'username': 'editme',
            'first_name': 'Edit',
            'last_name': 'Me',
            'email': 'edit@test.com',
            'role': '',
            'plan': '',
            'is_active': 'on',
            'brands': [str(brand.pk)],
            'default_brand': str(brand.pk),
            f'membership_role_{brand.pk}': BrandMembership.ROLE_DEALER,
        })
        self.assertRedirects(res, reverse('admin_users'))
        mem = BrandMembership.objects.get(user=user, brand=brand)
        self.assertEqual(mem.role, BrandMembership.ROLE_DEALER)

    def test_superuser_deletes_brand_user(self):
        brand = BusinessBrand.objects.create(name='Sil Marka', slug='sil-marka')
        user = User.objects.create_user(username='deleteme', password='x')
        BrandMembership.objects.create(user=user, brand=brand, role=BrandMembership.ROLE_MEMBER)
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_user_delete', kwargs={'pk': user.pk}))
        self.assertRedirects(res, reverse('admin_users'))
        self.assertFalse(User.objects.filter(username='deleteme').exists())

    def test_superuser_edits_brand_relationships(self):
        hq = BusinessBrand.objects.create(name='HQ Marka', slug='hq-marka', panel_kind=BusinessBrand.PANEL_HQ)
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_edit', kwargs={'pk': hq.pk}), {
            'name': 'HQ Güncel',
            'legal_name': 'HQ Ltd',
            'phone': '555',
            'host_slug': 'hq-guncel',
            'panel_kind': BusinessBrand.PANEL_HQ,
            'parent_brand': '',
            'tenant_routing': BusinessBrand.TENANT_SUBDOMAIN,
            'is_active': 'on',
        })
        self.assertEqual(res.status_code, 302)
        hq.refresh_from_db()
        self.assertEqual(hq.name, 'HQ Güncel')

    def test_superuser_changes_brand_permanent_url(self):
        hq = BusinessBrand.objects.create(name='URL Marka', slug='url-marka')
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_edit', kwargs={'pk': hq.pk}), {
            'owner': '',
            'name': 'URL Marka',
            'host_slug': 'golgede-yasam',
            'legal_name': '',
            'phone': '',
            'panel_kind': BusinessBrand.PANEL_HQ,
            'parent_brand': '',
            'tenant_routing': BusinessBrand.TENANT_SUBDOMAIN,
            'is_active': 'on',
        })
        self.assertEqual(res.status_code, 302)
        hq.refresh_from_db()
        self.assertEqual(hq.host_slug, 'golgede-yasam')
        self.assertEqual(hq.tenant_key, 'golgede-yasam')

    def test_superuser_rejects_duplicate_permanent_url(self):
        BusinessBrand.objects.create(name='İlk', slug='ilk-marka', host_slug='ortak-kod')
        second = BusinessBrand.objects.create(name='İkinci', slug='ikinci-marka')
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_edit', kwargs={'pk': second.pk}), {
            'owner': '',
            'name': 'İkinci',
            'host_slug': 'ortak-kod',
            'legal_name': '',
            'phone': '',
            'panel_kind': BusinessBrand.PANEL_HQ,
            'parent_brand': '',
            'tenant_routing': BusinessBrand.TENANT_SUBDOMAIN,
            'is_active': 'on',
        })
        self.assertEqual(res.status_code, 200)
        second.refresh_from_db()
        self.assertNotEqual(second.host_slug, 'ortak-kod')

    def test_superuser_views_reports(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(reverse('admin_reports')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin_reports_usage')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin_relations')).status_code, 200)

    def test_superuser_deletes_empty_brand(self):
        brand = BusinessBrand.objects.create(name='Boş Marka', slug='bos-marka')
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_delete', kwargs={'pk': brand.pk}), {
            'confirm_name': 'Boş Marka',
        })
        self.assertRedirects(res, reverse('admin_brands'))
        self.assertFalse(BusinessBrand.objects.filter(slug='bos-marka').exists())

    def test_superuser_system_role_urls_live(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(reverse('admin_roles')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin_role_create')).status_code, 200)

    def test_superuser_plan_crud(self):
        from common.module_plan import default_plan_module_seed

        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(reverse('admin_plans')).status_code, 200)
        from common.module_catalog import MODULE_KIND_APP, MODULE_KIND_INTEGRATION, MODULES

        app_slugs = {
            m['slug'] for m in MODULES
            if m['kind'] == MODULE_KIND_APP and not m['slug'].startswith('agency_') and m['slug'] != 'settings'
        }
        integration_slugs = {
            m['slug'] for m in MODULES if m['kind'] == MODULE_KIND_INTEGRATION
        }
        seed = default_plan_module_seed()
        modules = [s for s in seed if s in app_slugs]
        integrations = [s for s in seed if s in integration_slugs] + ['integration_weather']
        res = self.client.post(reverse('admin_plan_create'), {
            'name': 'Yönetim Test Plan',
            'price': '99.00',
            'max_hq_brands': 2,
            'max_dealer_panels': 1,
            'max_users_per_brand': 10,
            'max_customers_per_brand': 500,
            'is_active': 'on',
            'included_modules': modules,
            'included_integrations': integrations,
        })
        self.assertRedirects(res, reverse('admin_plans'))
        plan = Plan.objects.get(name='Yönetim Test Plan')
        self.assertEqual(plan.max_hq_brands, 2)
        self.assertIn('integration_weather', plan.included_module_slugs)
        res = self.client.post(reverse('admin_plan_edit', kwargs={'pk': plan.pk}), {
            'name': 'Pro Plus',
            'price': '149.00',
            'max_hq_brands': 3,
            'max_dealer_panels': 2,
            'max_users_per_brand': 10,
            'max_customers_per_brand': 500,
            'is_active': 'on',
            'included_modules': modules,
            'included_integrations': [s for s in seed if s in integration_slugs],
        })
        self.assertEqual(res.status_code, 302)
        plan.refresh_from_db()
        self.assertEqual(plan.name, 'Pro Plus')

    def test_superuser_cannot_be_brand_owner(self):
        from users.admin_services import reassign_brand_owner, strip_superuser_brand_memberships

        brand = BusinessBrand.objects.create(name='SA Block', slug='sa-block')
        BrandMembership.objects.create(
            user=self.superuser,
            brand=brand,
            role=BrandMembership.ROLE_OWNER,
        )
        owner = User.objects.create_user(username='realowner', password='x')
        with self.assertRaises(ValueError):
            reassign_brand_owner(brand, self.superuser)
        deleted = strip_superuser_brand_memberships(self.superuser)
        self.assertGreaterEqual(deleted, 1)
        self.assertFalse(
            BrandMembership.objects.filter(user=self.superuser, role=BrandMembership.ROLE_OWNER).exists()
        )

    def test_superuser_creates_billing_invoice(self):
        owner = User.objects.create_user(username='billowner', password='x')
        plan = Plan.objects.get(name='Ücretsiz Plan')
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_invoice_create'), {
            'user': owner.pk,
            'plan': plan.pk,
            'amount': '49.90',
            'status': 'paid',
        })
        self.assertRedirects(res, reverse('admin_invoices'))
        self.assertTrue(BillingInvoice.objects.filter(user=owner, plan=plan).exists())

    def test_superuser_brand_activate_and_deactivate(self):
        brand = BusinessBrand.objects.create(name='Toggle Marka', slug='toggle-marka')
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_deactivate', kwargs={'pk': brand.pk}))
        self.assertEqual(res.status_code, 302)
        brand.refresh_from_db()
        self.assertFalse(brand.is_active)
        res = self.client.post(reverse('admin_brand_activate', kwargs={'pk': brand.pk}))
        self.assertEqual(res.status_code, 302)
        brand.refresh_from_db()
        self.assertTrue(brand.is_active)

    def test_superuser_reassigns_brand_owner(self):
        owner1 = User.objects.create_user(username='own1', password='x')
        plan = Plan.objects.get(name='Ücretsiz Plan')
        owner2 = User.objects.create_user(username='own2', password='x', plan=plan)
        brand = BusinessBrand.objects.create(name='Reassign Marka', slug='reassign-marka')
        BrandMembership.objects.create(user=owner1, brand=brand, role=BrandMembership.ROLE_OWNER)
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_edit', kwargs={'pk': brand.pk}), {
            'owner': owner2.pk,
            'name': 'Reassign Marka',
            'legal_name': '',
            'phone': '',
            'host_slug': '',
            'panel_kind': BusinessBrand.PANEL_HQ,
            'parent_brand': '',
            'tenant_routing': BusinessBrand.TENANT_SUBDOMAIN,
            'is_active': 'on',
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(
            BrandMembership.objects.filter(
                user=owner2,
                brand=brand,
                role=BrandMembership.ROLE_OWNER,
            ).exists()
        )

    def test_superuser_creates_platform_admin(self):
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_user_create'), {
            'account_type': 'superuser',
            'username': 'platadmin',
            'first_name': 'Platform',
            'last_name': 'Admin',
            'email': 'plat@test.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'is_active': 'on',
        })
        self.assertRedirects(res, reverse('admin_users'))
        user = User.objects.get(username='platadmin')
        self.assertTrue(user.is_superuser)

    def test_last_superuser_cannot_demote_self(self):
        User.objects.filter(is_superuser=True).exclude(pk=self.superuser.pk).update(
            is_superuser=False,
            is_staff=False,
        )
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_user_edit', kwargs={'pk': self.superuser.pk}), {
            'username': 'super',
            'first_name': '',
            'last_name': '',
            'email': '',
            'role': '',
            'plan': '',
            'is_active': 'on',
            'is_superuser': '',
        })
        self.assertEqual(res.status_code, 200)
        self.superuser.refresh_from_db()
        self.assertTrue(self.superuser.is_superuser)

    def test_brand_inspect_creates_audit_log(self):
        brand = BusinessBrand.objects.create(name='Audit Marka', slug='audit-marka', is_active=True)
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_brand_inspect', kwargs={'pk': brand.pk}))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(
            PlatformAuditLog.objects.filter(
                action=PlatformAuditLog.ACTION_BRAND_INSPECT,
                brand=brand,
            ).exists()
        )

    def test_superuser_platform_pages(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(reverse('admin_site_settings')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin_audit_log')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin_invoices')).status_code, 200)
        export = self.client.get(reverse('admin_users_export'))
        self.assertEqual(export.status_code, 200)
        self.assertIn('text/csv', export['Content-Type'])
        usage_export = self.client.get(reverse('admin_reports_usage_export'))
        self.assertEqual(usage_export.status_code, 200)
        self.assertIn('text/csv', usage_export['Content-Type'])
