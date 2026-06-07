"""Giriş yapan kullanıcı için aktif marka oturumunu doğrular."""

from common.brand_scope import ensure_session_brand, set_active_brand, _brand_id_allowed_for_user


class ActiveBrandMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, 'user', None) and request.user.is_authenticated:
            tenant = getattr(request, 'tenant_brand', None)
            if tenant and _brand_id_allowed_for_user(request.user, tenant.pk):
                set_active_brand(request, tenant.pk)
            else:
                ensure_session_brand(request)
        return self.get_response(request)
