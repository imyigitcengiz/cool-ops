from django.test import SimpleTestCase

from common.erp_shell import erp_shell_theme_for_module, resolve_erp_shell_module


class ErpShellTests(SimpleTestCase):
    def test_resolve_panel_paths(self):
        self.assertEqual(resolve_erp_shell_module('/panel/'), 'panel')
        self.assertEqual(resolve_erp_shell_module('/panel/moduller/'), 'panel')

    def test_resolve_contact(self):
        self.assertEqual(resolve_erp_shell_module('/contact/musteriler/'), 'contact')

    def test_resolve_settings(self):
        self.assertEqual(resolve_erp_shell_module('/ayarlar/genel/'), 'settings')

    def test_theme_for_accounting(self):
        self.assertEqual(erp_shell_theme_for_module('accounting'), 'erp-theme-emerald')
