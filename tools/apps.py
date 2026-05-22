from django.apps import AppConfig


class ToolsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tools'
    verbose_name = 'Araçlar'

    def ready(self):
        import tools.signals  # noqa: F401

        try:
            from tools.whatsapp_bridge_autostart import schedule_bridge_autostart

            schedule_bridge_autostart()
        except Exception:
            import logging

            logging.getLogger(__name__).exception('WhatsApp köprüsü otomatik başlatma planlanamadı')
