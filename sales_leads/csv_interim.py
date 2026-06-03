"""Satış CSV — ara ödeme sütunlarını algılama ve içe aktarma."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from common.csv_io import parse_date_tr, parse_decimal
from common.csv_mapping import normalize_header


def is_interim_amount_header(header: str) -> bool:
    n = normalize_header(header)
    if 'ARA' not in n or 'ODEME' not in n:
        return False
    return 'TARIH' not in n and 'TARIHI' not in n


def is_interim_date_header(header: str) -> bool:
    n = normalize_header(header)
    if 'ARA' not in n or 'ODEME' not in n:
        return False
    return 'TARIH' in n or 'TARIHI' in n


def interim_column_index(header: str) -> int:
    n = normalize_header(header)
    match = re.search(r'(\d+)\s*$', n)
    return int(match.group(1)) if match else 1


def detect_interim_headers(headers: list[str]) -> list[dict]:
    """CSV başlıklarından ara ödeme sütunlarını listeler (sihirbaz bilgisi için)."""
    found: list[dict] = []
    for header in headers:
        if is_interim_date_header(header):
            found.append({'header': header, 'role': 'date', 'index': interim_column_index(header)})
        elif is_interim_amount_header(header):
            found.append({'header': header, 'role': 'amount', 'index': interim_column_index(header)})
    return sorted(found, key=lambda x: (x['index'], x['role'] == 'date'))


def has_interim_columns(headers: list[str]) -> bool:
    return any(is_interim_amount_header(h) for h in headers)


def _cell(raw: dict, key: str) -> str:
    for k, v in raw.items():
        if k == key:
            return (v or '').strip()
    return ''


def parse_interim_payments_from_row(
    raw: dict,
    *,
    default_date: date,
) -> list[tuple[Decimal, date]]:
    """Satırdaki ara ödeme tutar/tarih sütun çiftlerini döndürür."""
    amount_cols: dict[int, str] = {}
    date_cols: dict[int, str] = {}
    for key in raw:
        if is_interim_amount_header(key):
            amount_cols[interim_column_index(key)] = key
        elif is_interim_date_header(key):
            date_cols[interim_column_index(key)] = key

    payments: list[tuple[Decimal, date]] = []
    for idx in sorted(amount_cols):
        col = amount_cols[idx]
        amt = parse_decimal(_cell(raw, col))
        if not (amt and amt > 0):
            continue
        date_col = date_cols.get(idx)
        pay_date = default_date
        if date_col:
            pay_date = parse_date_tr(_cell(raw, date_col)) or default_date
        payments.append((amt, pay_date))
    return payments


INTERIM_IMPORT_HELP = (
    'Satış formundaki gibi ara ödemeler CSV’ye ek sütun olarak yazılır; sihirbazda ayrıca '
    'eşleştirmeniz gerekmez. Tek ödeme: «Ara ödeme tarihi» ve «Ara ödeme». Birden fazla: '
    '«Ara ödeme tarihi 2», «Ara ödeme 2» … Satış raporu CSV’sini indirip aynı başlıkları '
    'kullanabilirsiniz. Tarih boşsa satış tarihi alınır.'
)
