from django.core.management.base import BaseCommand

from tools.firm_directory import sync_all_partners_to_directory


class Command(BaseCommand):
    help = 'Çözüm ağı kayıtlarını firmalar rehberine senkronlar.'

    def handle(self, *args, **options):
        count = sync_all_partners_to_directory()
        self.stdout.write(self.style.SUCCESS(f'{count} çözüm ortağı rehbere işlendi.'))
