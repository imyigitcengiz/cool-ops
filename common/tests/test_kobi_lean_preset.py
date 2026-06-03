"""Sade KOBİ preset testleri."""

from django.test import TestCase

from common.kobi_lean_preset import (
    full_finance_extension_slugs,
    is_legacy_bloated_preset,
    lean_kobi_slugs,
)
from common.module_catalog import default_enabled_module_slugs
from common.module_particles import default_enabled_particle_slugs
from common.sector_catalog import sector_preset_all_slugs


class KobiLeanPresetTests(TestCase):
    def test_lean_slugs_core_modules_only(self):
        slugs = lean_kobi_slugs()
        self.assertIn('contact', slugs)
        self.assertIn('integration_whatsapp_bridge', slugs)
        self.assertNotIn('outreach', slugs)
        self.assertNotIn('integration_weather', slugs)

    def test_default_enabled_modules_match_lean(self):
        modules = default_enabled_module_slugs()
        for required in ('contact', 'services', 'accounting', 'settings', 'integration_whatsapp_bridge'):
            self.assertIn(required, modules)
        for optional in ('outreach', 'integration_data_harvest', 'p.accounting.projects'):
            self.assertNotIn(optional, modules)

    def test_montaj_sector_preset_is_lean(self):
        self.assertEqual(set(sector_preset_all_slugs('montaj_saha')), set(lean_kobi_slugs()))

    def test_legacy_bloated_detection(self):
        from common.kobi_lean_preset import LEGACY_BLOATED_MODULES, LEGACY_BLOATED_PARTICLES

        bloated = list(LEGACY_BLOATED_MODULES | LEGACY_BLOATED_PARTICLES)
        self.assertTrue(is_legacy_bloated_preset(bloated))
        self.assertFalse(is_legacy_bloated_preset(lean_kobi_slugs()))

    def test_default_particles_lean(self):
        particles = default_enabled_particle_slugs()
        self.assertIn('p.accounting.cash', particles)
        self.assertNotIn('p.accounting.stock', particles)
        self.assertNotIn('p.outreach.campaigns', particles)
