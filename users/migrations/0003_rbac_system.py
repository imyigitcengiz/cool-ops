from django.db import migrations, models
import django.db.models.deletion


PERMISSIONS = [
    ('access.home', 'Ana sayfa', 'Genel', 10),
    ('access.services', 'Servis modülü', 'Servis', 20),
    ('access.contact', 'Contact modülü', 'Contact', 30),
    ('access.sales', 'Satış modülü', 'Satış', 40),
    ('access.tools', 'Tools modülü', 'Tools', 50),
    ('access.settings', 'Sistem ayarları', 'Ayarlar', 60),
    ('services.manage', 'Servis kayıtları yönetimi', 'Servis', 70),
    ('contact.customers', 'Müşteri yönetimi', 'Contact', 80),
    ('contact.firms', 'Firma & etiket yönetimi', 'Contact', 90),
    ('contact.personnel', 'Personel & ekip yönetimi', 'Contact', 100),
    ('contact.payroll', 'Maaş ödemeleri', 'Contact', 110),
    ('contact.solution', 'Çözüm ağı yönetimi', 'Contact', 120),
    ('sales.manage', 'Satış kayıtları yönetimi', 'Satış', 130),
    ('tools.whatsapp', 'WhatsApp araçları', 'Tools', 140),
    ('tools.ai', 'Yapay zeka ayarları', 'Tools', 150),
    ('tools.backup', 'Yedekleme & geri yükleme', 'Tools', 160),
]

DEFAULT_ROLES = {
    'admin': {
        'name': 'Yönetici',
        'description': 'Tüm modüllere erişim.',
        'permissions': [p[0] for p in PERMISSIONS],
    },
    'operation': {
        'name': 'Operasyon',
        'description': 'Servis, contact ve operasyon araçları.',
        'permissions': [
            'access.home', 'access.services', 'access.contact', 'access.tools',
            'services.manage', 'contact.customers', 'contact.firms',
            'contact.personnel', 'contact.solution', 'tools.whatsapp',
        ],
    },
    'service': {
        'name': 'Servis Personeli',
        'description': 'Servis kayıtları.',
        'permissions': [
            'access.home', 'access.services', 'access.contact',
            'services.manage', 'contact.customers',
        ],
    },
    'sales': {
        'name': 'Satış Temsilcisi',
        'description': 'Satış kayıtları.',
        'permissions': [
            'access.home', 'access.sales', 'access.contact',
            'sales.manage', 'contact.customers', 'contact.payroll',
        ],
    },
    'accounting': {
        'name': 'Muhasebe',
        'description': 'Maaş ödemeleri.',
        'permissions': [
            'access.home', 'access.contact',
            'contact.customers', 'contact.payroll',
        ],
    },
}


def seed_rbac(apps, schema_editor):
    Permission = apps.get_model('users', 'Permission')
    Role = apps.get_model('users', 'Role')
    User = apps.get_model('users', 'User')

    perm_map = {}
    for codename, name, module, sort_order in PERMISSIONS:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={'name': name, 'module': module, 'sort_order': sort_order},
        )
        perm_map[codename] = perm

    role_map = {}
    for slug, data in DEFAULT_ROLES.items():
        role, _ = Role.objects.get_or_create(
            slug=slug,
            defaults={
                'name': data['name'],
                'description': data['description'],
                'is_system': True,
            },
        )
        role.permissions.set([perm_map[c] for c in data['permissions'] if c in perm_map])
        role_map[slug] = role

    for user in User.objects.all():
        legacy = getattr(user, 'role_legacy', None) or 'sales'
        if legacy in role_map:
            user.role_id = role_map[legacy].id
            user.save(update_fields=['role_id'])

    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Süper',
            'last_name': 'Admin',
            'email': 'admin@local',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'role_id': role_map.get('admin').id if role_map.get('admin') else None,
        },
    )
    if created:
        from django.contrib.auth.hashers import make_password
        admin_user.password = make_password('admin')
        admin_user.save(update_fields=['password'])
    else:
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.is_active = True
        admin_user.save()


def copy_role_to_legacy(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.select_related('role').all():
        user.role_legacy = user.role.slug if user.role_id else 'sales'
        user.save(update_fields=['role_legacy'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_userprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codename', models.CharField(max_length=80, unique=True)),
                ('name', models.CharField(max_length=120)),
                ('module', models.CharField(default='Genel', max_length=40)),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'İzin',
                'verbose_name_plural': 'İzinler',
                'ordering': ['module', 'sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=40, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_system', models.BooleanField(default=False, verbose_name='Sistem rolü')),
                ('permissions', models.ManyToManyField(blank=True, related_name='roles', to='users.permission')),
            ],
            options={
                'verbose_name': 'Rol',
                'verbose_name_plural': 'Roller',
                'ordering': ['name'],
            },
        ),
        migrations.RenameField(
            model_name='user',
            old_name='role',
            new_name='role_legacy',
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='users',
                to='users.role',
                verbose_name='Rol',
            ),
        ),
        migrations.RunPython(seed_rbac, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='user',
            name='role_legacy',
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'Kullanıcı', 'verbose_name_plural': 'Kullanıcılar'},
        ),
    ]
