from django.core.management.base import BaseCommand

from users.permission_sync import sync_permissions_to_db


class Command(BaseCommand):
    help = 'Katalogdaki izinleri veritabanına senkronize eder.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-system-roles',
            action='store_true',
            help='Sistem rollerinin izinlerini katalogdaki varsayılanlara sıfırlar.',
        )

    def handle(self, *args, **options):
        sync_permissions_to_db(reset_system_role_permissions=options['reset_system_roles'])
        self.stdout.write(self.style.SUCCESS('İzinler senkronize edildi.'))
