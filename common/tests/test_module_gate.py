"""Modül kapısı — kapalı modül/entegrasyon URL erişimi."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from common.kobi_lean_preset import lean_kobi_slugs
from common.module_runtime import get_enabled_module_slugs, module_route_allowed
from core_settings.models import SiteSettings
from users.models import Role

User = get_user_model()


class ModuleGateTests(TestCase):
    def setUp(self):
        role = Role.objects.filter(slug='service').first()
        self.user = User.objects.create_user(username='_gate', password='x')
        if role:
            self.user.role = role
            self.user.save()
        SiteSettings.objects.create(site_name='Gate Test')
        self.client = Client()
        self.client.force_login(self.user)

    def _slugs_without(self, *omit):
        return [s for s in get_enabled_module_slugs() if s not in omit]

    def test_closed_integration_blocks_tools_media_url(self):
        settings = SiteSettings.objects.first()
        settings.enabled_module_slugs = self._slugs_without('integration_media')
        settings.save()
        self.assertFalse(module_route_allowed('integration_media'))
        response = self.client.get('/tools/medya/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/panel/abonelik/', response.url)
        self.assertIn('#moduller', response.url)

    def test_closed_whatsapp_blocks_bridge_url(self):
        settings = SiteSettings.objects.first()
        settings.enabled_module_slugs = self._slugs_without('integration_whatsapp_bridge')
        settings.save()
        response = self.client.get('/tools/whatsapp-baglan/')
        self.assertEqual(response.status_code, 302)

    def test_outreach_closed_hides_whatsapp_api_even_if_integration_on(self):
        settings = SiteSettings.objects.first()
        slugs = list(get_enabled_module_slugs()) + ['integration_whatsapp_api']
        slugs = [s for s in slugs if s != 'outreach']
        settings.enabled_module_slugs = slugs
        settings.save()
        self.assertFalse(module_route_allowed('integration_whatsapp_api'))
        response = self.client.get('/tools/whatsapp-api/')
        self.assertEqual(response.status_code, 302)

    def test_outreach_closed_hides_bulk_messaging_even_if_integration_on(self):
        settings = SiteSettings.objects.first()
        slugs = list(get_enabled_module_slugs()) + ['integration_bulk_messaging']
        slugs = [s for s in slugs if s != 'outreach']
        settings.enabled_module_slugs = slugs
        settings.save()
        self.assertFalse(module_route_allowed('integration_bulk_messaging'))
        response = self.client.get('/iletisim/kampanyalar/')
        self.assertEqual(response.status_code, 302)

    def test_bulk_messaging_closed_blocks_campaign_url(self):
        settings = SiteSettings.objects.first()
        slugs = [s for s in get_enabled_module_slugs() if s != 'integration_bulk_messaging']
        if 'outreach' not in slugs:
            slugs.append('outreach')
        settings.enabled_module_slugs = slugs
        settings.save()
        self.assertFalse(module_route_allowed('integration_bulk_messaging'))
        response = self.client.get('/iletisim/kampanyalar/')
        self.assertEqual(response.status_code, 302)

    def test_whatsapp_bridge_works_without_outreach(self):
        role = Role.objects.filter(slug='admin').first()
        if role:
            self.user.role = role
            self.user.save()
        settings = SiteSettings.objects.first()
        settings.enabled_module_slugs = lean_kobi_slugs()
        settings.save()
        self.assertTrue(module_route_allowed('integration_whatsapp_bridge'))
        response = self.client.get('/tools/whatsapp-baglan/')
        self.assertEqual(response.status_code, 200)

    def test_payables_particle_closed_blocks_route(self):
        from common.kobi_lean_preset import lean_kobi_slugs

        settings = SiteSettings.objects.first()
        slugs = [s for s in lean_kobi_slugs() if s != 'p.accounting.payables']
        if 'accounting' not in slugs:
            slugs.append('accounting')
        settings.enabled_module_slugs = slugs
        settings.save()
        response = self.client.get('/muhasebe/borclar/')
        self.assertEqual(response.status_code, 302)

    def test_firma_kazi_blocked_when_data_harvest_closed(self):
        settings = SiteSettings.objects.first()
        settings.enabled_module_slugs = self._slugs_without('integration_data_harvest')
        settings.save()
        response = self.client.get('/contact/firma-kazi/')
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.url, '/contact/firma-kazi/')

    def test_contact_sidebar_hides_closed_integration(self):
        settings = SiteSettings.objects.first()
        settings.enabled_module_slugs = self._slugs_without('integration_media')
        settings.save()
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Medya Kütüphanesi')

    def test_tools_hub_stays_accessible_when_integrations_closed(self):
        settings = SiteSettings.objects.first()
        settings.enabled_module_slugs = self._slugs_without(
            'integration_whatsapp_bridge',
            'integration_whatsapp_api',
            'integration_media',
            'integration_weather',
        )
        settings.save()
        response = self.client.get('/tools/')
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('/panel/moduller/', response.url)
