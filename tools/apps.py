import os
import sys

from django.apps import AppConfig


def _should_autostart_whatsapp_bridge() -> bool:
    argv = sys.argv
    if not any(cmd in argv for cmd in ('runserver', 'daphne')):
        return False
    skip_commands = (
        'migrate', 'makemigrations', 'test', 'shell', 'collectstatic',
        'createsuperuser', 'flush', 'check',
    )
    if any(cmd in argv for cmd in skip_commands):
        return False
    if 'runserver' in argv:
        if '--noreload' in argv:
            return True
        return os.environ.get('RUN_MAIN') == 'true'
    return True


class ToolsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tools'
    verbose_name = 'Araçlar'

    def ready(self):
        if not _should_autostart_whatsapp_bridge():
            return
        from django.conf import settings

        if not getattr(settings, 'WHATSAPP_BRIDGE_AUTO_START', True):
            return
        try:
            from tools.whatsapp_bridge_runner import bridge_reachable, try_spawn_bridge_process

            if not bridge_reachable(timeout=0.5):
                try_spawn_bridge_process()
        except Exception:
            import logging
            logging.getLogger(__name__).exception('WhatsApp köprüsü otomatik başlatılamadı')
