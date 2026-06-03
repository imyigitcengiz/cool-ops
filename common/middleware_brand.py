"""Giriş yapan kullanıcı için aktif marka oturumunu doğrular."""

from common.brand_scope import ensure_session_brand


class ActiveBrandMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, 'user', None) and request.user.is_authenticated:
            ensure_session_brand(request)
        return self.get_response(request)
