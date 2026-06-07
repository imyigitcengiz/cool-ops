"""Özel 403 / 404 hata sayfaları."""

from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.test import Client, RequestFactory, TestCase, override_settings

from common.views import page_not_found, permission_denied
from core_settings.models import SiteSettings
from users.models import Role

User = get_user_model()


def _request_with_user(path='/'):
    factory = RequestFactory()
    request = factory.get(path)
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    AuthenticationMiddleware(lambda r: None).process_request(request)
    return request


class ErrorPageHandlerTests(TestCase):
    def setUp(self):
        SiteSettings.objects.create(site_name='Hata Test')
        self.client = Client()

    def test_404_handler_renders_custom_page(self):
        request = _request_with_user('/olmayan-adres/')
        response = page_not_found(request, exception=None)
        self.assertEqual(response.status_code, 404)
        content = response.content.decode()
        self.assertIn('404', content)
        self.assertIn('Sayfa bulunamadı', content)
        self.assertIn('/olmayan-adres/', content)

    def test_403_handler_renders_custom_page(self):
        request = _request_with_user('/gizli/')
        response = permission_denied(
            request,
            exception=PermissionDenied('Bu alana erişemezsiniz.'),
        )
        self.assertEqual(response.status_code, 403)
        content = response.content.decode()
        self.assertIn('403', content)
        self.assertIn('Erişim engellendi', content)
        self.assertIn('Bu alana erişemezsiniz.', content)

    @override_settings(DEBUG=False)
    def test_unknown_url_returns_404_when_debug_off(self):
        response = self.client.get('/bu-sayfa-kesinlikle-yok-404-test/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Sayfa bulunamadı', status_code=404)

    def test_permission_middleware_renders_403_page(self):
        role = Role.objects.create(slug='no-access', name='No Access', is_system=False)
        user = User.objects.create_user(username='denied', password='x', role=role)
        self.client.force_login(user)
        response = self.client.get('/panel/ekip/')
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Erişim engellendi', status_code=403)
