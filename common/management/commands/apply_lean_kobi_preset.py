"""Site modül listesini sade KOBİ çekirdeğine indirir."""

from django.core.management.base import BaseCommand

from common.kobi_lean_preset import is_legacy_bloated_preset, lean_kobi_slugs
from core_settings.models import SiteSettings


class Command(BaseCommand):
    help = 'Modül listesini sade KOBİ presetine uygular (eski tam paket veya --force).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mevcut özelleştirmeleri yok say; doğrudan lean preset uygula.',
        )

    def handle(self, *args, **options):
        settings = SiteSettings.objects.first()
        if not settings:
            settings = SiteSettings.objects.create()

        stored = list(settings.enabled_module_slugs or [])
        lean = lean_kobi_slugs()

        if options['force'] or not stored or is_legacy_bloated_preset(stored):
            settings.enabled_module_slugs = lean
            settings.save(update_fields=['enabled_module_slugs'])
            self.stdout.write(self.style.SUCCESS(
                f'Sade KOBİ preset uygulandı ({len(lean)} slug).'
            ))
            return

        self.stdout.write(self.style.WARNING(
            'Mevcut modül listesi özelleştirilmiş görünüyor; değişiklik yapılmadı. '
            'Zorlamak için --force kullanın.'
        ))
