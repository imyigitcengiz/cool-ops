import re

PLACE_ID_RE = re.compile(r'^ChIJ[\w-]+$')
# (0232), (0212) vb. sabit hat alan kodları
LANDLINE_AREA_PARENS_RE = re.compile(r'\(\s*0[234]\d{2}\s*\)')


def normalize_phone(raw):
    if not raw or raw == '-':
        return ''
    digits = ''.join(c for c in str(raw) if c.isdigit())
    if len(digits) < 10:
        return ''
    if digits.startswith('0'):
        digits = '90' + digits[1:]
    elif len(digits) == 10:
        digits = '90' + digits
    return digits if len(digits) >= 11 else ''


def is_turkish_landline(raw, normalized=None):
    """Sabit hat (0232, 0212, 0312 …) — WhatsApp'a uygun değil."""
    raw_s = str(raw or '').strip()
    if not raw_s or raw_s == '-':
        return False
    if LANDLINE_AREA_PARENS_RE.search(raw_s):
        return True
    digits = ''.join(c for c in raw_s if c.isdigit())
    if digits.startswith('0') and len(digits) >= 3:
        if digits[1] in '234' and not digits.startswith('05'):
            return True
    norm = normalized if normalized is not None else normalize_phone(raw_s)
    if norm.startswith('90') and len(norm) >= 12:
        if norm[2] != '5':
            return True
    return False


def is_whatsapp_eligible(raw, normalized=None):
    norm = normalized if normalized is not None else normalize_phone(raw)
    if not norm:
        return False
    if is_turkish_landline(raw, norm):
        return False
    return True


def whatsapp_url(phone):
    if not is_whatsapp_eligible(phone):
        return '-'
    normalized = normalize_phone(phone)
    if not normalized:
        return '-'
    return f'https://wa.me/{normalized}'
