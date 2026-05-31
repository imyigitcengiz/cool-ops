import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import OperationalError

from common.db import uses_postgresql


class Command(BaseCommand):
    help = 'PostgreSQL bağlantısı hazır olana kadar bekler (Docker başlangıcı).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Maksimum bekleme süresi (saniye)',
        )

    def handle(self, *args, **options):
        if not uses_postgresql():
            return

        timeout = max(1, options['timeout'])
        deadline = time.time() + timeout
        last_error = None

        while time.time() < deadline:
            try:
                connections['default'].ensure_connection()
                self.stdout.write(self.style.SUCCESS('PostgreSQL bağlantısı hazır.'))
                return
            except OperationalError as exc:
                last_error = exc
                time.sleep(1)

        raise CommandError(f'PostgreSQL {timeout}s içinde hazır olmadı: {last_error}')
