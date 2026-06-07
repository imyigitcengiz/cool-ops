"""Bayi kullanıcılarının üst platform paneline erişimini engeller."""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from common.brand_access import path_blocked_for_dealer, resolve_post_login_url, user_is_dealer_only
from common.middleware import _is_api_request


class DealerPlatformGuardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and user_is_dealer_only(user):
            path = request.path
            if path_blocked_for_dealer(path):
                if _is_api_request(request):
                    return JsonResponse(
                        {'ok': False, 'error': 'Bayi hesapları üst panele erişemez.'},
                        status=403,
                    )
                messages.warning(
                    request,
                    'Bayi hesapları yalnızca kendi panel adreslerinden giriş yapabilir; üst platform paneli kapalıdır.',
                )
                return redirect(resolve_post_login_url(request, user))
        return self.get_response(request)
