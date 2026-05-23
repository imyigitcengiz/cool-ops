"""Üretimde medya dosyası sunumu (/media/...) — Unicode yol ve volume uyumu."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET


@require_GET
def serve_media_file(request, path: str):
    media_root = Path(settings.MEDIA_ROOT).resolve()
    if not media_root.is_dir():
        raise Http404('Medya dizini yok.')

    # URL decode sonrası gelen path (django zaten decode eder)
    relative = path.lstrip('/')
    target = (media_root / relative).resolve()

    try:
        target.relative_to(media_root)
    except ValueError:
        raise Http404('Geçersiz yol.') from None

    if not target.is_file():
        raise Http404('Dosya bulunamadı.')

    content_type, _ = mimetypes.guess_type(target.name)
    response = FileResponse(
        target.open('rb'),
        content_type=content_type or 'application/octet-stream',
    )
    response['Cache-Control'] = 'public, max-age=86400'
    return response
