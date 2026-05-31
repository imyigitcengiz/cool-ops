"""Mevcut gelir/gider kayıtlarını varsayılan kasa hesabına bağla."""

from django.db import migrations


def assign_default_cash_account(apps, schema_editor):
    CashAccount = apps.get_model('core_settings', 'CashAccount')
    FinanceRecord = apps.get_model('core_settings', 'FinanceRecord')
    CashSettings = apps.get_model('core_settings', 'CashSettings')

    default = CashAccount.objects.filter(is_default=True).first()
    if not default:
        legacy = CashSettings.objects.first()
        opening = legacy.opening_balance if legacy else 0
        default = CashAccount.objects.create(
            name='Ana kasa',
            account_type='cash',
            opening_balance=opening,
            is_default=True,
            is_active=True,
        )
    FinanceRecord.objects.filter(cash_account__isnull=True).update(cash_account=default)


class Migration(migrations.Migration):

    dependencies = [
        ('core_settings', '0042_enable_finance_extensions'),
    ]

    operations = [
        migrations.RunPython(assign_default_cash_account, migrations.RunPython.noop),
    ]
