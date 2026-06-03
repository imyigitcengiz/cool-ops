"""CSV sütun eşleştirme — otomatik tanıma ve canonical satır dönüşümü."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def normalize_header(value: str) -> str:
    s = (value or '').strip().upper()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^A-Z0-9]+', '_', s)
    return s.strip('_')


@dataclass(frozen=True)
class ImportField:
    key: str
    label: str
    required: bool = False
    aliases: tuple[str, ...] = ()


def auto_map_headers(csv_headers: list[str], fields: list[ImportField]) -> dict[str, str]:
    """canonical_key → csv header adı (model verbose_name ile uyumlu etiketler öncelikli)."""
    normalized_csv = {normalize_header(h): h for h in csv_headers if h}
    mapping: dict[str, str] = {}

    for field in fields:
        candidates = [field.label, field.key, *field.aliases]
        for cand in candidates:
            norm = normalize_header(cand)
            if norm in normalized_csv:
                mapping[field.key] = normalized_csv[norm]
                break
        if field.key not in mapping:
            label_norm = normalize_header(field.label)
            for norm, original in normalized_csv.items():
                if norm and (norm == label_norm or norm in label_norm or label_norm in norm):
                    mapping[field.key] = original
                    break
    return mapping


def apply_column_mapping(
    rows: list[dict[str, str]],
    mapping: dict[str, str | None],
) -> list[dict[str, str]]:
    """Her satırı canonical alan anahtarlarına dönüştür."""
    out: list[dict[str, str]] = []
    for row in rows:
        mapped: dict[str, str] = {}
        for key, header in mapping.items():
            if header and header in row:
                mapped[key] = (row.get(header) or '').strip()
            else:
                mapped[key] = ''
        out.append(mapped)
    return out


def boost_import_mapping(
    import_type: str,
    headers: list[str],
    mapping: dict[str, str | None],
) -> dict[str, str | None]:
    """Eşleştirilmemiş ürün / müşteri adı sütunlarını başlıktan tahmin et."""
    out = dict(mapping)
    normalized = {normalize_header(h): h for h in headers if h}

    if import_type in ('customers', 'sales') and not out.get('products'):
        for norm, original in normalized.items():
            if not norm:
                continue
            if 'URUN' in norm or 'PRODUCT' in norm or ('SATIN' in norm and 'ALDI' in norm):
                out['products'] = original
                break

    if import_type == 'customers' and not out.get('name'):
        for norm, original in normalized.items():
            if norm in ('MUSTERI_ADI', 'AD_SOYAD', 'MUSTERI', 'AD', 'NAME', 'MUSTERI_ADI_SOYADI'):
                out['name'] = original
                break
            if 'MUSTERI' in norm and 'URUN' not in norm:
                out['name'] = original
                break

    if import_type == 'sales' and not out.get('customer_name'):
        for norm, original in normalized.items():
            if norm in ('MUSTERI_ADI', 'AD_SOYAD', 'MUSTERI', 'AD', 'NAME'):
                out['customer_name'] = original
                break
            if 'MUSTERI' in norm and 'URUN' not in norm:
                out['customer_name'] = original
                break

    if import_type == 'customers':
        if not out.get('project'):
            for norm, original in normalized.items():
                if 'PROJE' in norm and 'ID' not in norm:
                    out['project'] = original
                    break
        if not out.get('total'):
            for norm, original in normalized.items():
                if norm in ('TOPLAM', 'TUTAR', 'SATIS_TUTARI') or 'TOPLAM' in norm:
                    out['total'] = original
                    break
        if not out.get('down_payment'):
            for norm, original in normalized.items():
                if 'PESINAT' in norm or 'PESIN' in norm:
                    out['down_payment'] = original
                    break
        if not out.get('date'):
            for norm, original in normalized.items():
                if norm in ('TARIH', 'TARIHI') or ('SATIS' in norm and 'TARIH' in norm):
                    out['date'] = original
                    break

    return out


def parse_mapping_payload(raw) -> dict[str, str | None]:
    """JSON veya form dict → canonical_key: csv_header | None."""
    if not raw:
        return {}
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str):
        import json
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    else:
        return {}
    out: dict[str, str | None] = {}
    for key, val in data.items():
        if val in (None, '', '__skip__'):
            out[str(key)] = None
        else:
            out[str(key)] = str(val).strip()
    return out
