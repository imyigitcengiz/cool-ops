"""Modül aç/kapa API testleri."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from common.module_runtime import is_module_installed
from core_settings.models import SiteSettings


class ModuleToggleApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        role = __import__('users.models', fromlist=['Role']).Role.objects.filter(slug='admin').first()
        self.user = User.objects.create_user(username='_modtog', password='x')
        if role:
            self.user.role = role
            self.user.save()
        SiteSettings.objects.create(site_name='Test')
        self.client.force_login(self.user)

    def test_toggle_off_on_without_page_reload(self):
        from common.module_runtime import get_enabled_module_slugs

        slug = 'integration_weather'
        settings = SiteSettings.objects.first()
        enabled = list(get_enabled_module_slugs())
        if slug not in enabled:
            settings.enabled_module_slugs = enabled + [slug]
            settings.save()
        self.assertTrue(is_module_installed(slug))

        off = self.client.post('/panel/moduller/toggle/', {'module_slug': slug})
        self.assertEqual(off.status_code, 200)
        data = off.json()
        self.assertTrue(data['ok'])
        self.assertFalse(data['installed'])
        self.assertFalse(is_module_installed(slug))

        on = self.client.post('/panel/moduller/toggle/', {'module_slug': slug})
        self.assertEqual(on.status_code, 200)
        self.assertTrue(on.json()['installed'])

    def test_disable_montaj_particle_persists(self):
        from common.module_runtime import get_enabled_module_slugs, is_particle_enabled

        particle = 'p.accounting.projects'
        settings = SiteSettings.objects.first()
        modules = list(get_enabled_module_slugs())
        if 'accounting' not in modules:
            settings.enabled_module_slugs = modules + ['accounting', particle]
            settings.save()
        elif particle not in settings.enabled_module_slugs:
            settings.enabled_module_slugs = list(settings.enabled_module_slugs) + [particle]
            settings.save()
        self.assertTrue(is_particle_enabled(particle))

        off = self.client.post('/panel/moduller/toggle/', {'particle_slug': particle})
        self.assertTrue(off.json()['ok'])
        settings.refresh_from_db()
        self.assertNotIn(particle, settings.enabled_module_slugs)
        self.assertFalse(is_particle_enabled(particle))

    def test_toggle_requires_settings_perm(self):
        User = get_user_model()
        role = __import__('users.models', fromlist=['Role']).Role.objects.filter(slug='service').first()
        user = User.objects.create_user(username='_svc', password='x')
        if role:
            user.role = role
            user.save()
        self.client.force_login(user)
        resp = self.client.post('/panel/moduller/toggle/', {'module_slug': 'contact'})
        self.assertEqual(resp.status_code, 403)

    def test_toggle_particle_off_on(self):
        from common.module_runtime import get_enabled_particle_slugs, is_particle_enabled

        slug = 'p.contact.customers'
        settings = SiteSettings.objects.first()
        modules = list(__import__('common.module_runtime', fromlist=['get_enabled_module_slugs']).get_enabled_module_slugs())
        if 'contact' not in modules:
            settings.enabled_module_slugs = modules + ['contact']
            settings.save()

        if slug not in get_enabled_particle_slugs():
            settings.enabled_module_slugs = modules + [slug]
            settings.save()
        self.assertTrue(is_particle_enabled(slug))

        off = self.client.post('/panel/moduller/toggle/', {'particle_slug': slug})
        self.assertEqual(off.status_code, 200)
        self.assertTrue(off.json()['ok'])
        self.assertFalse(off.json()['enabled'])
        self.assertFalse(is_particle_enabled(slug))

        on = self.client.post('/panel/moduller/toggle/', {'particle_slug': slug})
        self.assertEqual(on.status_code, 200)
        self.assertTrue(on.json()['enabled'])

    def test_particle_requires_parent_module(self):
        from common.module_runtime import get_enabled_module_slugs

        settings = SiteSettings.objects.first()
        modules = [s for s in get_enabled_module_slugs() if s != 'contact']
        settings.enabled_module_slugs = modules
        settings.save()
        resp = self.client.post('/panel/moduller/toggle/', {'particle_slug': 'p.contact.customers'})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['ok'])

    def test_cannot_disable_last_module(self):
        settings = SiteSettings.objects.first()
        settings.enabled_module_slugs = ['settings']
        settings.save()
        resp = self.client.post('/panel/moduller/toggle/', {'module_slug': 'settings'})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['ok'])
