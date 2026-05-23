"""Yükleme yolları — sunucuda güvenli dosya adları (Unicode/Traefik uyumu)."""

from pathlib import Path


def site_logo_upload_to(instance, filename):
    ext = Path(filename).suffix.lower()
    if ext not in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
        ext = '.jpg'
    return f'site/logo{ext}'
