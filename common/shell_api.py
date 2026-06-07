"""Uygulama kabuğu API — hızlı arama ve bildirimler."""

from __future__ import annotations

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from common.decorators import json_auth_required
from common.quick_search import build_quick_search_results, search_entities
from users.notifications import (
    list_notifications,
    mark_all_read,
    mark_read,
    refresh_system_notifications,
    unread_count,
)


@json_auth_required
@require_GET
def quick_search_api(request):
    q = (request.GET.get('q') or '').strip()
    pages = build_quick_search_results(request.user, q, limit=12, request=request)
    records = search_entities(request.user, q, limit=6, request=request) if len(q) >= 2 else []
    return JsonResponse({'ok': True, 'pages': pages, 'records': records})


@json_auth_required
@require_GET
def notifications_api(request):
    refresh_system_notifications(request.user)
    return JsonResponse({
        'ok': True,
        'unread': unread_count(request.user),
        'items': list_notifications(request.user, limit=25),
    })


@json_auth_required
@require_POST
def notification_mark_read_api(request, pk: int):
    ok = mark_read(request.user, pk)
    return JsonResponse({'ok': ok, 'unread': unread_count(request.user)})


@json_auth_required
@require_POST
def notifications_mark_all_read_api(request):
    count = mark_all_read(request.user)
    return JsonResponse({'ok': True, 'marked': count, 'unread': 0})
