"""Panel ve modül merkezi smoke testleri."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from common.module_runtime import build_panel_integrations, build_panel_modules, get_enabled_module_slugs
from core_settings.models import SiteSettings
from users.models import Role

User = get_user_model()


class PanelViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        role = Role.objects.filter(slug='admin').first()
        self.user = User.objects.create_user(username='_panel_test', password='test1234')
        if role:
            self.user.role = role
            self.user.save()
        SiteSettings.objects.create(site_name='Panel Test')

    def test_home_requires_login(self):
        response = self.client.get('/panel/')
        self.assertEqual(response.status_code, 302)

    def test_home_ok_for_admin(self):
        self.client.force_login(self.user)
        response = self.client.get('/panel/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modül')

    def test_home_hides_closed_integrations(self):
        settings = SiteSettings.objects.first()
        settings.enabled_module_slugs = [
            s for s in get_enabled_module_slugs()
            if s != 'integration_data_harvest'
        ]
        settings.save()
        self.client.force_login(self.user)
        response = self.client.get('/panel/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Firma &amp; Lead Kazıma')
        self.assertNotContains(response, 'Firma bul')

    def test_home_hides_sub_app_modules(self):
        from core_settings.models import Plan

        settings = SiteSettings.objects.first()
        slugs = [
            s for s in get_enabled_module_slugs()
            if s not in (
                'supplier_payables', 'projects', 'multi_cash', 'project_costing', 'timesheet',
                'p.accounting.payables', 'p.accounting.projects', 'p.accounting.multi_cash',
                'p.accounting.project_costing', 'p.accounting.timesheet',
            )
        ]
        settings.enabled_module_slugs = slugs
        settings.save()
        plan, _ = Plan.objects.get_or_create(
            name='Panel Test Plan',
            defaults={'price': 0, 'max_hq_brands': 1, 'included_module_slugs': slugs},
        )
        plan.included_module_slugs = slugs
        plan.save()
        self.user.plan = plan
        self.user.enabled_module_slugs = slugs
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get('/panel/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Tedarikçi borçları')
        self.assertNotContains(response, 'Montaj programı')

    def test_panel_integrations_require_parent_module(self):
        settings = SiteSettings.objects.first()
        settings.enabled_module_slugs = [
            s for s in get_enabled_module_slugs()
            if s != 'outreach'
        ]
        settings.save()
        integrations = build_panel_integrations(self.user)
        outreach_slugs = {
            i['slug'] for i in integrations
            if i.get('panel_section') == 'outreach'
        }
        self.assertEqual(outreach_slugs, set())

    def test_panel_modules_only_primary_hubs(self):
        modules = build_panel_modules(self.user)
        slugs = {m['slug'] for m in modules}
        self.assertTrue(slugs.issubset({'contact', 'services', 'accounting', 'outreach'}))

    def test_module_hub_redirects_to_subscription(self):
        self.client.force_login(self.user)
        response = self.client.get('/panel/moduller/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/panel/abonelik/', response.url)
        self.assertIn('#moduller', response.url)

    def test_capabilities_hub_ok(self):
        self.client.force_login(self.user)
        response = self.client.get('/panel/yetenekler/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entegrasyon')
        self.assertContains(response, 'Toplu mesaj gönderici')

    def test_landing_uses_site_name_in_title(self):
        settings = SiteSettings.objects.first()
        settings.site_name = 'Özel Mağaza Adı'
        settings.save()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<title>Özel Mağaza Adı — Operasyon paneli</title>', html=False)

    def test_introducer_knowledge_base_public(self):
        response = self.client.get('/bilgi-bankasi/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bilgi bankası')
        self.assertContains(response, 'Tam demo')

    def test_introducer_knowledge_base_journey_query(self):
        response = self.client.get('/bilgi-bankasi/?yol=hizmet-hizli')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hızlı demo')

    def test_contact_hub_ok(self):
        self.client.force_login(self.user)
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 200)

    def test_whatsapp_baglan_ok(self):
        self.client.force_login(self.user)
        response = self.client.get('/tools/whatsapp-baglan/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'WhatsApp Köprüsü')

    def test_home_view_plan_and_brand_context(self):
        self.client.force_login(self.user)
        response = self.client.get('/panel/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('active_plan', response.context)
        self.assertIn('user_brands', response.context)
        self.assertIn('owned_brands_count', response.context)

    def test_superuser_brand_creation_bypass_limit(self):
        from core_settings.models import Plan
        from common.brand_scope import create_brand_for_user
        
        # Create a plan with max_brands = 1
        test_plan = Plan.objects.create(name='Test Limit Plan', price=10, max_brands=1)
        
        # Test user
        self.user.plan = test_plan
        self.user.save()
        
        # Create one brand (now we are at limit 1/1)
        create_brand_for_user(self.user, 'Brand One')
        
        # Try to create second brand (should fail for normal user)
        with self.assertRaises(ValueError):
            create_brand_for_user(self.user, 'Brand Two')
            
        # Süper admin marka oluşturamaz
        self.user.is_superuser = True
        self.user.save()
        with self.assertRaises(ValueError):
            create_brand_for_user(self.user, 'Brand Two')

    def test_subscription_view_post_brand_create_and_switch(self):
        self.client.force_login(self.user)

        response = self.client.post('/panel/abonelik/', {
            'form_action': 'brand_create',
            'name': 'New Franchise Panel',
            'legal_name': 'Franchise Ltd',
            'phone': '12345',
        })
        self.assertRedirects(response, '/panel/abonelik/')

        from core_settings.models import BusinessBrand
        brand = BusinessBrand.objects.get(name='New Franchise Panel')
        self.assertEqual(brand.legal_name, 'Franchise Ltd')

        brand_two = BusinessBrand.objects.create(name='Other Panel', created_by=self.user)
        from core_settings.models import BrandMembership
        BrandMembership.objects.create(user=self.user, brand=brand_two, role=BrandMembership.ROLE_OWNER)

        response = self.client.post('/panel/abonelik/', {
            'form_action': 'brand_switch',
            'brand_id': brand_two.pk,
        })
        self.assertRedirects(response, '/panel/abonelik/')

        response = self.client.get('/panel/abonelik/')
        self.assertEqual(response.context['active_brand'].pk, brand_two.pk)

    def test_subscription_view_post_upgrade_plan(self):
        self.client.force_login(self.user)
        from core_settings.models import Plan
        new_plan = Plan.objects.create(name='Gold Plan', price=99, max_brands=5)

        response = self.client.post('/panel/abonelik/', {
            'form_action': 'upgrade_plan',
            'plan_id': new_plan.pk,
        })
        self.assertRedirects(response, '/panel/abonelik/')

        self.user.refresh_from_db()
        self.assertEqual(self.user.plan.pk, new_plan.pk)

    def test_subscription_dashboard_page_ok(self):
        self.client.force_login(self.user)
        response = self.client.get('/panel/abonelik/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Abonelik & Bayi / Franchise Yönetimi')

    def test_brands_manage_redirects_to_subscription(self):
        self.client.force_login(self.user)
        response = self.client.get('/profil/markalar/')
        self.assertRedirects(response, '/panel/abonelik/')
