import json
import os
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from common.db import uses_sqlite


class Command(BaseCommand):
    help = 'SQLite dosyasındaki veriyi aktif PostgreSQL veritabanına taşır.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            default='',
            help='Kaynak db.sqlite3 yolu (varsayılan: proje kökü veya DJANGO_SQLITE_SOURCE)',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Onay sormadan mevcut PostgreSQL verisinin üzerine yazar',
        )

    def handle(self, *args, **options):
        if uses_sqlite():
            raise CommandError(
                'Hedef veritabanı SQLite. Önce POSTGRES_HOST veya DATABASE_URL ayarlayın.'
            )

        source = options['source'].strip() or os.environ.get('DJANGO_SQLITE_SOURCE', '').strip()
        if not source:
            source = str(Path(settings.BASE_DIR) / 'db.sqlite3')
        source_path = Path(source).resolve()
        if not source_path.is_file():
            raise CommandError(f'SQLite dosyası bulunamadı: {source_path}')

        if not options['noinput']:
            confirm = input(
                f'{source_path} → PostgreSQL taşınacak; mevcut PG verisi silinecek. Devam? [y/N] '
            )
            if confirm.strip().lower() not in ('y', 'yes', 'evet', 'e'):
                self.stdout.write('İptal edildi.')
                return

        settings.DATABASES['sqlite_source'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': source_path,
            'TIME_ZONE': None,
            'OPTIONS': {},
            'HOST': '',
            'PORT': '',
            'USER': '',
            'PASSWORD': '',
            'CONN_MAX_AGE': 0,
            'CONN_HEALTH_CHECKS': False,
            'AUTOCOMMIT': True,
            'ATOMIC_REQUESTS': False,
        }
        connections.databases['sqlite_source'] = settings.DATABASES['sqlite_source']

        try:
            self.stdout.write('SQLite verisi dışa aktarılıyor…')
            buffer = StringIO()
            call_command(
                'dumpdata',
                database='sqlite_source',
                indent=2,
                natural_foreign=True,
                natural_primary=True,
                exclude=['contenttypes', 'auth.permission'],
                stdout=buffer,
            )
            buffer.seek(0)
            fixture = json.loads(buffer.read())
            if not fixture:
                raise CommandError('SQLite dosyası boş görünüyor.')

            self.stdout.write(f'{len(fixture)} kayıt bulundu. PostgreSQL hazırlanıyor…')
            call_command('migrate', '--noinput', verbosity=0)
            call_command('flush', '--noinput', verbosity=0)

            from users.models import Permission

            Permission.objects.all().delete()

            tmp_path = None
            try:
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.json',
                    delete=False,
                    encoding='utf-8',
                ) as handle:
                    tmp_path = handle.name
                    json.dump(fixture, handle, ensure_ascii=False, indent=2)

                with transaction.atomic():
                    call_command('loaddata', tmp_path, verbosity=0)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            try:
                call_command('sync_permissions', verbosity=0)
            except Exception:
                pass

            self.stdout.write(
                self.style.SUCCESS(
                    f'Taşıma tamamlandı — {len(fixture)} kayıt PostgreSQL\'e yüklendi.'
                )
            )
        finally:
            connections.databases.pop('sqlite_source', None)
            settings.DATABASES.pop('sqlite_source', None)
