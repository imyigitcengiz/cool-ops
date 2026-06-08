"""Panel kaydı ve yönlendirme testleri."""

from django.test import TestCase
from django.urls import reverse

from common.module_catalog import MODULE_KIND_APP, MODULES, PANEL_ID_KOBIPOS, PANEL_ID_KOBIOPS
from common.panel_registry import (
    PANEL_KOBIOPS,
    PANEL_KOBIPOS,
    all_panels,
    apps_for_panel,
    panel_by_id,
    panel_for_module,
    panel_url,
)
from common.panel_routing import (
    is_restaurant_plan,
    resolve_plan_default_panel,
    restaurant_panel_url,
)


class PanelRegistryTests(TestCase):
    def test_all_panels_registered(self):
        panels = all_panels()
        self.assertEqual(len(panels), 2)
        ids = {p['id'] for p in panels}
        self.assertEqual(ids, {PANEL_KOBIOPS, PANEL_KOBIPOS})

    def test_every_app_module_has_valid_panel_id(self):
        for mod in MODULES:
            if mod['kind'] != MODULE_KIND_APP:
                continue
            panel_id = mod.get('panel_id')
            self.assertIsNotNone(panel_id, msg=f"{mod['slug']} panel_id eksik")
            self.assertIsNotNone(panel_by_id(panel_id), msg=f"{mod['slug']} geçersiz panel_id")

    def test_restaurant_module_maps_to_kobipos(self):
        panel = panel_for_module('restaurant')
        self.assertIsNotNone(panel)
        self.assertEqual(panel['id'], PANEL_KOBIPOS)

    def test_contact_module_maps_to_kobiops(self):
        panel = panel_for_module('contact')
        self.assertIsNotNone(panel)
        self.assertEqual(panel['id'], PANEL_KOBIOPS)

    def test_franchise_panel_url_uses_registry_prefix(self):
        from common.panel_registry import franchise_panel_url
        self.assertEqual(franchise_panel_url('ankara-01'), '/restoran/franchise?code=ankara-01')
        self.assertIsNone(franchise_panel_url(''))

    def test_panel_url_reverse(self):
        self.assertEqual(panel_url(PANEL_KOBIOPS), reverse('home'))
        self.assertEqual(panel_url(PANEL_KOBIPOS), reverse('restaurant_hub'))
        self.assertEqual(restaurant_panel_url(), '/restoran/')

    def test_apps_for_panel(self):
        kobiops_apps = apps_for_panel(PANEL_ID_KOBIOPS)
        kobipos_apps = apps_for_panel(PANEL_ID_KOBIPOS)
        kobiops_slugs = {m['slug'] for m in kobiops_apps}
        kobipos_slugs = {m['slug'] for m in kobipos_apps}
        self.assertIn('contact', kobiops_slugs)
        self.assertIn('restaurant', kobipos_slugs)
        self.assertNotIn('restaurant', kobiops_slugs)


class PanelRoutingTests(TestCase):
    def _plan(self, slugs):
        class _FakePlan:
            included_module_slugs = list(slugs)

        return _FakePlan()

    def test_restaurant_plan_resolves_kobipos(self):
        plan = self._plan(['restaurant', 'contact'])
        self.assertTrue(is_restaurant_plan(plan))
        self.assertEqual(resolve_plan_default_panel(plan), PANEL_KOBIPOS)

    def test_enterprise_plan_resolves_kobiops(self):
        plan = self._plan(['contact', 'services', 'accounting'])
        self.assertFalse(is_restaurant_plan(plan))
        self.assertEqual(resolve_plan_default_panel(plan), PANEL_KOBIOPS)

    def test_restaurant_with_services_is_kobiops(self):
        plan = self._plan(['restaurant', 'services'])
        self.assertFalse(is_restaurant_plan(plan))
        self.assertEqual(resolve_plan_default_panel(plan), PANEL_KOBIOPS)
