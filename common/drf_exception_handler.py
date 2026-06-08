"""DRF merkezi hata yanıtı — internal detay sızıntısını önler."""

from __future__ import annotations

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

GENERIC_MESSAGE = 'İşlem sırasında bir hata oluştu. Lütfen tekrar deneyin.'


def safe_api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    logger.exception('Unhandled API exception', exc_info=exc)
    data = {'error': GENERIC_MESSAGE}
    if settings.DEBUG:
        data['detail'] = str(exc)
    return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
