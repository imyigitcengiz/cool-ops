"""İstekten marka/bayi kiracısını çözümler ve yol önekini ayıklar."""

from common.brand_scope import set_active_brand, _brand_id_allowed_for_user
from common.tenant import resolve_request_tenant, strip_tenant_path


class BrandTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant, path_prefix = resolve_request_tenant(request)
        request.tenant_brand = tenant
        request.tenant_path_prefix = path_prefix or ''
        strip_tenant_path(request, path_prefix)

        if tenant and getattr(request, 'user', None) and request.user.is_authenticated:
            if _brand_id_allowed_for_user(request.user, tenant.pk):
                set_active_brand(request, tenant.pk)

        return self.get_response(request)
