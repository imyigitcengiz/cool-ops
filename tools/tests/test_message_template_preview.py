from django.test import SimpleTestCase

from tools.collections import DEFAULT_TEMPLATE, preview_message_template


class MessageTemplatePreviewTests(SimpleTestCase):
    def test_preview_replaces_placeholders(self):
        template = 'Merhaba {firma}, {bolge} bölgesinde {puan} puan.'
        preview = preview_message_template(template)
        self.assertIn('Örnek Klima Ltd.', preview)
        self.assertIn('Kadıköy', preview)
        self.assertIn('4.8', preview)
        self.assertNotIn('{firma}', preview)

    def test_preview_uses_default_when_empty(self):
        preview = preview_message_template('')
        self.assertIn('Örnek Klima Ltd.', preview)
        self.assertEqual(preview, preview_message_template(DEFAULT_TEMPLATE))
