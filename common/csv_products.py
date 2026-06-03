"""CSV ürün listesi — ProductOption eşlemesi."""

from __future__ import annotations


def parse_product_names_cell(raw: str) -> list[str]:
    """Hücredeki ürün adlarını ayırır (| ; , veya tek değer)."""
    text = (raw or '').strip()
    if not text or text in ('-', '—'):
        return []
    normalized = text.replace('\n', '|')
    for sep in ('|', ';'):
        if sep in normalized:
            return [p.strip() for p in normalized.split(sep) if p.strip() and p.strip() not in ('-', '—')]
    if ',' in normalized:
        return [p.strip() for p in normalized.split(',') if p.strip()]
    return [text]


def resolve_product_options(names: list[str]):
    """Ürün adlarını ProductOption kayıtlarına bağlar (aynı isimde çift kayıt toleranslı)."""
    from core_settings.models import ProductOption

    result = []
    seen: set[str] = set()
    for name in names:
        clean = name.strip()
        key = clean.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        obj = ProductOption.objects.filter(name__iexact=clean).order_by('pk').first()
        if obj is None:
            obj = ProductOption.objects.create(name=clean)
        result.append(obj)
    return result
