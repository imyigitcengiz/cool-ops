from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from users.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = 'Süper admin hesabını (admin/admin) oluşturur veya günceller.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-password',
            action='store_true',
            help='admin kullanıcısının şifresini admin olarak sıfırlar',
        )

    def handle(self, *args, **options):
        admin_role = Role.objects.filter(slug='admin').first()
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Süper',
                'last_name': 'Admin',
                'email': 'admin@local',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'role': admin_role,
            },
        )
        if not created:
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            if admin_role and not user.role_id:
                user.role = admin_role

        if created or options['reset_password']:
            user.password = make_password('admin')
            self.stdout.write(self.style.WARNING('Şifre: admin'))

        user.save()
        action = 'oluşturuldu' if created else 'güncellendi'
        self.stdout.write(self.style.SUCCESS(f'Süper admin {action} (kullanıcı: admin)'))
