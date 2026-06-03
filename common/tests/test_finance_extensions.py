"""Yol haritası muhasebe modülleri smoke testleri."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from core_settings.models import SupplierPayable
from core_settings.payables import build_payables_context, create_payable, record_payment

User = get_user_model()


class FinanceExtensionsTests(TestCase):
    def setUp(self):
        from common.kobi_lean_preset import full_finance_extension_slugs
        from core_settings.models import SiteSettings

        settings, _ = SiteSettings.objects.get_or_create(
            defaults={'site_name': 'Test'},
        )
        settings.enabled_module_slugs = full_finance_extension_slugs()
        settings.save(update_fields=['enabled_module_slugs'])
        self.client = Client()
        role = __import__('users.models', fromlist=['Role']).Role.objects.filter(slug='admin').first()
        self.user = User.objects.create_user(username='_fin_ext', password='test1234')
        if role:
            self.user.role = role
            self.user.save()
        self.client.force_login(self.user)
        from common.brand_scope import system_default_brand
        from core_settings.models import BrandMembership

        self.brand = system_default_brand()
        if self.brand:
            BrandMembership.objects.get_or_create(
                user=self.user,
                brand=self.brand,
                defaults={'role': BrandMembership.ROLE_OWNER, 'is_default': True},
            )

    def _brand_kwargs(self):
        if self.brand:
            return {'brand_id': self.brand.pk}
        return {}

    def test_payables_page_ok(self):
        response = self.client.get('/muhasebe/borclar/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tedarikçi')

    def test_cash_accounts_page_ok(self):
        response = self.client.get('/muhasebe/hesaplar/')
        self.assertEqual(response.status_code, 200)

    def test_project_costing_page_ok(self):
        response = self.client.get('/muhasebe/proje-karlilik/')
        self.assertEqual(response.status_code, 200)

    def test_e_export_page_ok(self):
        response = self.client.get('/muhasebe/dis-aktarim/')
        self.assertEqual(response.status_code, 200)

    def test_timesheet_page_ok(self):
        response = self.client.get('/muhasebe/zaman/')
        self.assertEqual(response.status_code, 200)

    def test_projects_page_ok(self):
        response = self.client.get('/muhasebe/projeler/')
        self.assertEqual(response.status_code, 200)

    def test_payable_payment_creates_expense(self):
        payable = create_payable(supplier_name='ABC Ltd', amount=Decimal('1000.00'))
        record_payment(payable, Decimal('400.00'), self.user)
        payable.refresh_from_db()
        self.assertEqual(payable.paid_amount, Decimal('400.00'))
        ctx = build_payables_context()
        self.assertEqual(ctx['payable_count'], 1)
        self.assertEqual(ctx['payable_total'], Decimal('600.00'))

    def test_project_costing_reflects_linked_expense(self):
        from customers.models import Customer
        from sales_leads.models import SalesLead
        from core_settings.models import FinanceRecord
        from django.utils import timezone

        customer = Customer.objects.create(name='Test Müşteri', **self._brand_kwargs())
        lead = SalesLead.objects.create(
            customer=customer,
            sale_date=timezone.localdate(),
            project='Test proje',
            sale_amount=Decimal('5000'),
        )
        FinanceRecord.objects.create(
            record_type=FinanceRecord.TYPE_EXPENSE,
            category='material',
            title='Malzeme',
            amount=Decimal('500'),
            record_date=timezone.localdate(),
            sales_lead=lead,
            recorded_by=self.user,
            **self._brand_kwargs(),
        )
        costing = self.client.get('/muhasebe/proje-karlilik/')
        self.assertEqual(costing.status_code, 200)
        self.assertContains(costing, '500')
        self.assertContains(costing, '4500')

    def test_finance_csv_export_includes_account_and_sales(self):
        from customers.models import Customer
        from sales_leads.models import SalesLead
        from core_settings.models import FinanceRecord, CashAccount
        from django.utils import timezone

        account = CashAccount.objects.create(name='Test Banka', account_type='bank', opening_balance=0)
        customer = Customer.objects.create(name='CSV Müşteri', **self._brand_kwargs())
        lead = SalesLead.objects.create(
            customer=customer,
            sale_date=timezone.localdate(),
            project='CSV proje',
            sale_amount=Decimal('1000'),
        )
        FinanceRecord.objects.create(
            record_type=FinanceRecord.TYPE_EXPENSE,
            category='material',
            title='CSV gider',
            amount=Decimal('100'),
            record_date=timezone.localdate(),
            cash_account=account,
            sales_lead=lead,
            recorded_by=self.user,
            **self._brand_kwargs(),
        )
        period = timezone.localdate().strftime('%Y-%m')
        response = self.client.get(f'/muhasebe/gelir-gider/export-csv/?period={period}')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8-sig')
        self.assertIn('Test Banka', body)
        self.assertIn('CSV gider', body)
        self.assertIn(str(lead.pk), body)

    def test_finance_csv_import_with_sales_id(self):
        from customers.models import Customer
        from sales_leads.models import SalesLead
        from core_settings.models import FinanceRecord
        from django.utils import timezone
        from io import BytesIO

        customer = Customer.objects.create(name='Import Müşteri')
        lead = SalesLead.objects.create(
            customer=customer,
            sale_date=timezone.localdate(),
            project='Imp',
            sale_amount=Decimal('2000'),
        )
        csv_text = (
            'TÜR;KATEGORİ;AÇIKLAMA;TUTAR;TARİH;HESAP;SATIŞ_ID;SATIŞ_ETİKET;PROJE;NOT\n'
            f'gider;malzeme;İthalat satır;250,00;{timezone.localdate().strftime("%d.%m.%Y")};;{lead.pk};;;\n'
        )
        uploaded = BytesIO(csv_text.encode('utf-8-sig'))
        uploaded.name = 'test.csv'
        response = self.client.post(
            '/muhasebe/gelir-gider/import-csv/',
            {'file': uploaded, '_redirect_period': timezone.localdate().strftime('%Y-%m')},
        )
        self.assertEqual(response.status_code, 302)
        rec = FinanceRecord.objects.filter(title='İthalat satır').first()
        self.assertIsNotNone(rec)
        self.assertEqual(rec.sales_lead_id, lead.pk)
        self.assertEqual(rec.category, 'material')
