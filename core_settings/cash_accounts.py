"""Çoklu kasa ve banka hesapları."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Q, Sum

from core_settings.models import CashAccount, CashSettings, FinanceRecord


@dataclass
class AccountBalance:
    account: CashAccount
    income: Decimal
    expense: Decimal
    current_balance: Decimal


def ensure_default_account() -> CashAccount:
    default = CashAccount.objects.filter(is_default=True, is_active=True).first()
    if default:
        return default
    legacy = CashSettings.objects.first()
    opening = legacy.opening_balance if legacy else Decimal('0')
    return CashAccount.objects.create(
        name='Ana kasa',
        account_type=CashAccount.TYPE_CASH,
        opening_balance=opening,
        is_default=True,
        is_active=True,
    )


def build_account_balance(account: CashAccount) -> AccountBalance:
    base = Q(cash_account=account)
    if account.is_default:
        base = base | Q(cash_account__isnull=True)
    income = FinanceRecord.objects.filter(
        base,
        record_type=FinanceRecord.TYPE_INCOME,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    expense = FinanceRecord.objects.filter(
        base,
        record_type=FinanceRecord.TYPE_EXPENSE,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    current = account.opening_balance + income - expense
    return AccountBalance(account=account, income=income, expense=expense, current_balance=current)


def build_accounts_context() -> dict:
    ensure_default_account()
    accounts = CashAccount.objects.filter(is_active=True).order_by('-is_default', 'name')
    rows = [build_account_balance(acc) for acc in accounts]
    total = sum((row.current_balance for row in rows), Decimal('0'))
    return {
        'account_rows': rows,
        'accounts_total_balance': total,
        'account_type_choices': CashAccount.TYPE_CHOICES,
    }


def create_account(*, name: str, account_type: str, opening_balance: Decimal, is_default: bool = False) -> CashAccount:
    if is_default:
        CashAccount.objects.filter(is_default=True).update(is_default=False)
    return CashAccount.objects.create(
        name=name.strip(),
        account_type=account_type,
        opening_balance=opening_balance,
        is_default=is_default,
        is_active=True,
    )
