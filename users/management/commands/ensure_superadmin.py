import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from users.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = 'İlk kurulumda süper admin oluşturur (varsayılan: admin/admin). Mevcut hesabın şifresini değiştirmez.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-password',
            action='store_true',
            help='admin kullanıcısının şifresini yeni rastgele değerle sıfırlar',
        )

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists() and not options['reset_password']:
            return

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
            password = os.environ.get('DJANGO_SUPERADMIN_PASSWORD', '').strip() or 'admin'
            user.password = make_password(password)
            data_dir = Path(os.environ.get('DATA_DIR', '/data'))
            pwd_file = data_dir / '.initial_admin_password'
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
                pwd_file.write_text(
                    f'username: admin\npassword: {password}\n',
                    encoding='utf-8',
                )
                os.chmod(pwd_file, 0o600)
                pwd_hint = str(pwd_file)
            except OSError:
                pwd_hint = '(dosyaya yazılamadı)'

            if password == 'admin':
                self.stdout.write(
                    self.style.WARNING(
                        f'İlk giriş — kullanıcı: admin, şifre: admin (kayıt: {pwd_hint})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'İlk giriş — kullanıcı: admin, şifre: {password} (kayıt: {pwd_hint})'
                    )
                )

        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS('Süper admin oluşturuldu (kullanıcı: admin)'))
        elif options['reset_password']:
            self.stdout.write(self.style.SUCCESS('Süper admin şifresi sıfırlandı (kullanıcı: admin)'))
