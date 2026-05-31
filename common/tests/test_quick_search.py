from django.contrib.auth import get_user_model
from django.test import TestCase

from common.quick_search import QUICK_SEARCH_ITEMS, build_quick_search_results
from users.models import Role, UserNotification
from users.notifications import notify_user, refresh_system_notifications


class QuickSearchTests(TestCase):
    def test_all_items_have_string_url_name(self):
        for item in QUICK_SEARCH_ITEMS:
            self.assertIsInstance(item.url_name, (str, type(None)))
            if item.url_name is not None:
                self.assertIsInstance(item.url_name, str)
            self.assertIsInstance(item.perms_any, tuple)
            for perm in item.perms_any:
                self.assertIsInstance(perm, str)

    def test_search_returns_valid_urls_for_superuser(self):
        user = get_user_model().objects.create_superuser('qs_admin', 'qs@test.local', 'pass')
        results = build_quick_search_results(user, 'maaş', limit=5)
        self.assertTrue(results)
        for row in results:
            self.assertTrue(row['url'].startswith('/'))
            self.assertIsInstance(row['url'], str)

    def test_rbac_user_gets_filtered_results(self):
        role = Role.objects.create(slug='qs_sales', name='QS Satış')
        role.permissions.set([])
        user = get_user_model().objects.create_user('qs_sales', password='pass', role=role)
        all_results = build_quick_search_results(user, '', limit=50)
        self.assertEqual(all_results, [])


class NotificationTests(TestCase):
    def test_dedupe_does_not_duplicate_after_mark_read(self):
        user = get_user_model().objects.create_user('notif_user', password='pass')
        first = notify_user(user, title='Test', dedupe_key='test-key')
        self.assertIsNotNone(first)
        first.is_read = True
        first.save(update_fields=['is_read'])
        second = notify_user(user, title='Test güncellendi', dedupe_key='test-key')
        self.assertEqual(UserNotification.objects.filter(user=user, dedupe_key='test-key').count(), 1)
        self.assertEqual(second.pk, first.pk)
        self.assertEqual(second.title, 'Test güncellendi')

    def test_refresh_throttled(self):
        user = get_user_model().objects.create_superuser('notif_admin', 'n@test.local', 'pass')
        refresh_system_notifications(user)
        count_after_first = UserNotification.objects.filter(user=user).count()
        refresh_system_notifications(user)
        count_after_second = UserNotification.objects.filter(user=user).count()
        self.assertEqual(count_after_first, count_after_second)
