"""Marka ekip yönetimi ve süper admin abonelik listesi."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from common.brand_scope import create_brand_for_user
from common.brand_team import assignable_roles_queryset
from core_settings.models import BrandMembership, Plan, SiteSettings
from users.models import Permission, Role

User = get_user_model()


class BrandTeamTests(TestCase):
    def setUp(self):
        self.client = Client()
        SiteSettings.objects.create(site_name='Team Test')
        Plan.objects.get_or_create(name='Ücretsiz Plan', defaults={'price': 0, 'max_brands': 3})
        role = Role.objects.filter(slug='admin').first()
        self.owner = User.objects.create_user(username='owner1', password='test1234', email='owner@test.com')
        if role:
            self.owner.role = role
            self.owner.save()
        self.brand = create_brand_for_user(self.owner, 'HQ Panel')

        self.member = User.objects.create_user(username='member1', password='test1234')
        if role:
            self.member.role = role
            self.member.save()
        BrandMembership.objects.create(
            user=self.member,
            brand=self.brand,
            role=BrandMembership.ROLE_MEMBER,
        )

        self.superuser = User.objects.create_superuser(username='super1', password='test1234', email='super@test.com')

    def test_owner_can_access_brand_team_users(self):
        self.client.force_login(self.owner)
        response = self.client.get('/panel/ekip/kullanicilar/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ekip Yönetimi')
        self.assertContains(response, 'member1')

    def test_member_cannot_access_brand_team(self):
        self.client.force_login(self.member)
        response = self.client.get('/panel/ekip/kullanicilar/')
        self.assertEqual(response.status_code, 302)

    def test_super_admin_lists_platform_users_with_owner_filter(self):
        outsider = User.objects.create_user(username='outsider', password='test1234')
        self.client.force_login(self.superuser)
        response = self.client.get('/yonetim/kullanicilar/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'owner1')
        self.assertContains(response, 'member1')
        self.assertContains(response, 'outsider')

        filtered = self.client.get('/yonetim/kullanicilar/?tur=owner')
        self.assertContains(filtered, 'owner1')
        self.assertNotContains(filtered, 'member1')
        self.assertNotContains(filtered, 'outsider')

    def test_owner_cannot_assign_admin_role(self):
        admin_role = Role.objects.filter(slug='admin').first()
        if not admin_role:
            admin_role = Role.objects.create(
                slug='admin',
                name='Yönetici',
                is_system=True,
                scope=Role.SCOPE_PLATFORM_SYSTEM,
            )
        else:
            admin_role.scope = Role.SCOPE_PLATFORM_SYSTEM
            admin_role.save(update_fields=['scope'])
        self.assertNotIn(admin_role, list(assignable_roles_queryset(self.owner)))

        self.client.force_login(self.owner)
        response = self.client.post('/panel/ekip/kullanicilar/yeni/', {
            'username': 'hacker',
            'email': 'hack@test.com',
            'first_name': 'Hack',
            'last_name': 'User',
            'role': admin_role.pk,
            'is_active': True,
            'password1': 'pass12345',
            'password2': 'pass12345',
            'brand': self.brand.pk,
            'membership_role': BrandMembership.ROLE_MEMBER,
            'is_default_brand': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='hacker').exists())

    def test_owner_cannot_grant_backup_permission_on_custom_role(self):
        backup_perm, _ = Permission.objects.get_or_create(
            codename='tools.backup',
            defaults={'name': 'Backup', 'module': 'Süper Admin', 'kind': 'action', 'sort_order': 0},
        )
        self.client.force_login(self.owner)
        response = self.client.post('/panel/ekip/roller/yeni/', {
            'name': 'Yedek Rol',
            'slug': 'yedek-rol',
            'description': 'test',
            'permissions': [str(backup_perm.pk)],
        })
        self.assertRedirects(response, '/panel/ekip/roller/')
        role = Role.objects.get(slug='yedek-rol')
        self.assertFalse(role.permissions.filter(codename='tools.backup').exists())

    def test_platform_system_roles_not_assignable_by_owner(self):
        Role.objects.update_or_create(
            slug='admin',
            defaults={
                'name': 'Yönetici',
                'scope': Role.SCOPE_PLATFORM_SYSTEM,
                'is_system': True,
            },
        )
        platform_ids = set(
            Role.objects.filter(scope=Role.SCOPE_PLATFORM_SYSTEM).values_list('pk', flat=True)
        )
        assignable_ids = set(assignable_roles_queryset(self.owner).values_list('pk', flat=True))
        self.assertFalse(platform_ids & assignable_ids)

    def test_owner_can_create_team_user(self):
        staff_role = Role.objects.filter(slug='operation').first()
        if not staff_role:
            staff_role = Role.objects.create(
                slug='operation',
                name='Operasyon',
                is_system=True,
                scope=Role.SCOPE_APP_PRESET,
                app_id=Role.APP_KOBIOPS,
            )
        else:
            staff_role.scope = Role.SCOPE_APP_PRESET
            staff_role.app_id = Role.APP_KOBIOPS
            staff_role.save(update_fields=['scope', 'app_id'])
        self.client.force_login(self.owner)
        response = self.client.post('/panel/ekip/kullanicilar/yeni/', {
            'username': 'newstaff',
            'email': 'staff@test.com',
            'first_name': 'Yeni',
            'last_name': 'Personel',
            'role': staff_role.pk,
            'is_active': True,
            'password1': 'pass12345',
            'password2': 'pass12345',
            'brand': self.brand.pk,
            'membership_role': BrandMembership.ROLE_MEMBER,
            'is_default_brand': True,
        })
        self.assertRedirects(response, '/panel/ekip/kullanicilar/')
        new_user = User.objects.get(username='newstaff')
        self.assertTrue(
            BrandMembership.objects.filter(user=new_user, brand=self.brand).exists()
        )
