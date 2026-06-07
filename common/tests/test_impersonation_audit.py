"""Impersonate denetim kaydı — dahili API (UI kaldırıldı)."""

from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from common.brand_scope import create_brand_for_user
from core_settings.models import SiteSettings
from users.impersonation import start_impersonation, stop_impersonation
from users.models import ImpersonationAudit

User = get_user_model()


def _request_with_session(factory, user):
    request = factory.post('/')
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    request.user = user
    return request


class ImpersonationAuditTests(TestCase):
    def setUp(self):
        SiteSettings.objects.create(site_name='Audit Test')
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(username='super', password='test1234')
        self.owner = User.objects.create_user(username='owner', password='test1234')
        create_brand_for_user(self.owner, 'Audit HQ')

    def test_impersonation_creates_audit_records(self):
        request = _request_with_session(self.factory, self.superuser)
        start_impersonation(request, self.owner)

        self.assertEqual(ImpersonationAudit.objects.filter(action=ImpersonationAudit.ACTION_START).count(), 1)
        entry = ImpersonationAudit.objects.get(action=ImpersonationAudit.ACTION_START)
        self.assertEqual(entry.actor_id, self.superuser.pk)
        self.assertEqual(entry.target_id, self.owner.pk)

        request.user = self.owner
        request.impersonator = self.superuser
        stop_impersonation(request)
        self.assertEqual(ImpersonationAudit.objects.filter(action=ImpersonationAudit.ACTION_STOP).count(), 1)
