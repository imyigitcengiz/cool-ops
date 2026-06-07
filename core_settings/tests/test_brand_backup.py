import gzip
import json
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from common.brand_scope import create_brand_for_user
from core_settings.backup import (
    BRAND_BACKUP_FORMAT_V1,
    export_brand_backup_response,
    import_brand_backup_file,
)
from core_settings.models import BusinessBrand, PriorityOption, SiteSettings, StatusOption
from core_settings.status_defaults import ensure_default_statuses
from customers.models import Customer
from services.models import ServiceRecord

User = get_user_model()


class BrandBackupTests(TestCase):
    def setUp(self):
        SiteSettings.objects.create(site_name='Brand Backup Test')
        ensure_default_statuses()
        self.owner = User.objects.create_user(username='brandowner', password='test1234')
        self.brand = create_brand_for_user(self.owner, 'Kaynak Marka')
        self.target = BusinessBrand.objects.create(name='Hedef Marka', slug='hedef-marka', is_active=True)
        self.status = StatusOption.objects.first()
        self.priority, _ = PriorityOption.objects.get_or_create(
            name='normal',
            defaults={'color': '#64748b'},
        )
        self.customer = Customer.objects.create(
            brand=self.brand,
            name='Test Müşteri',
            phone='555',
        )
        self.service = ServiceRecord.objects.create(
            brand=self.brand,
            customer=self.customer,
            status=self.status,
            priority=self.priority,
            notes='Yedek test',
        )

    def _export_payload(self) -> bytes:
        response = export_brand_backup_response(self.brand.pk)
        return response.content

    def test_export_and_import_replace(self):
        raw = gzip.decompress(self._export_payload())
        payload = json.loads(raw.decode('utf-8'))
        self.assertEqual(payload['format'], BRAND_BACKUP_FORMAT_V1)
        self.assertGreaterEqual(payload['record_count'], 2)

        uploaded = SimpleUploadedFile(
            'backup.json.gz',
            self._export_payload(),
            content_type='application/gzip',
        )
        Customer.objects.filter(brand=self.brand).delete()
        self.assertEqual(Customer.objects.filter(brand=self.brand).count(), 0)

        ok, msg = import_brand_backup_file(
            uploaded,
            self.brand.pk,
            replace_existing=True,
        )
        self.assertTrue(ok, msg)
        self.assertEqual(Customer.objects.filter(brand=self.brand).count(), 1)
        self.assertEqual(ServiceRecord.objects.filter(brand=self.brand).count(), 1)

    def test_import_into_other_brand(self):
        uploaded = SimpleUploadedFile(
            'backup.json.gz',
            self._export_payload(),
            content_type='application/gzip',
        )
        ok, msg = import_brand_backup_file(
            uploaded,
            self.target.pk,
            replace_existing=True,
        )
        self.assertTrue(ok, msg)
        self.assertEqual(Customer.objects.filter(brand=self.target).count(), 1)
        self.assertEqual(ServiceRecord.objects.filter(brand=self.target).count(), 1)
        self.assertEqual(Customer.objects.filter(brand=self.brand).count(), 1)

    def test_rejects_full_system_backup_in_brand_import(self):
        payload = {
            'format': 'cool-ops-backup-v2',
            'fixture': [],
        }
        uploaded = SimpleUploadedFile(
            'full.json',
            json.dumps(payload).encode('utf-8'),
            content_type='application/json',
        )
        ok, msg = import_brand_backup_file(uploaded, self.target.pk)
        self.assertFalse(ok)
        self.assertIn('marka yedeği', msg.lower())

    def test_import_accepts_gz_extension_only(self):
        """macOS/Safari dosya seçicide .json.gz çoğu zaman yalnızca .gz olarak görünür."""
        uploaded = SimpleUploadedFile(
            'cool-ops-panel-kaynak-marka-20260101.json.gz',
            self._export_payload(),
            content_type='application/gzip',
        )
        ok, msg = import_brand_backup_file(
            uploaded,
            self.target.pk,
            replace_existing=True,
        )
        self.assertTrue(ok, msg)
        self.assertEqual(Customer.objects.filter(brand=self.target).count(), 1)
