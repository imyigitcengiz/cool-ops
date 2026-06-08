"""Süresi dolmuş aboneliklerde yazma ve hassas okuma işlemlerini engeller."""

from django.utils.deprecation import MiddlewareMixin
from rest_framework.authtoken.models import Token

from restaurant.api.plan_limits import enforce_brand_write_access, get_plan_status, plan_expired_response
from restaurant.compat import get_api_profile

API_PREFIX = '/restoran/api/'

EXEMPT_PATHS = (
    f'{API_PREFIX}auth/login/',
    f'{API_PREFIX}auth/register/',
    f'{API_PREFIX}auth/register-staff/',
    f'{API_PREFIX}auth/logout/',
    f'{API_PREFIX}auth/me/',
    f'{API_PREFIX}auth/session-bridge/',
    f'{API_PREFIX}auth/seed-super-admin/',
    f'{API_PREFIX}auth/plan-status/',
    f'{API_PREFIX}auth/payment-providers/',
    f'{API_PREFIX}auth/invoices/',
    f'{API_PREFIX}franchise/login/',
    f'{API_PREFIX}franchise/logout/',
    f'{API_PREFIX}payments/stripe/webhook/',
    f'{API_PREFIX}payments/stripe/verify/',
    f'{API_PREFIX}payments/iyzico/callback/',
)

SENSITIVE_GET_PREFIXES = (
    f'{API_PREFIX}report-stats/',
    f'{API_PREFIX}low-stock/',
    f'{API_PREFIX}customers/',
    f'{API_PREFIX}orders/',
    f'{API_PREFIX}dashboard-stats/',
    f'{API_PREFIX}cash-transactions/',
    f'{API_PREFIX}expenses/',
)

WRITE_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')


def _authenticate_token_user(request):
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        return user
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Token '):
        key = auth_header[6:].strip()
        try:
            token = Token.objects.select_related('user').get(key=key)
            request.user = token.user
            return token.user
        except Token.DoesNotExist:
            pass
    return None


def enforce_sensitive_read_block(request):
    user = _authenticate_token_user(request)
    if not user:
        return None
    profile = get_api_profile(user, request)
    from restaurant.api.security import is_api_superuser
    if is_api_superuser(user):
        return None
    brand = profile.brand
    if not brand:
        return None
    plan_info = get_plan_status(brand)
    if plan_info['can_write']:
        return None
    return plan_expired_response(plan_info)


class RestaurantPlanEnforcementMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        path = request.path
        if not path.startswith(API_PREFIX):
            return None
        for exempt in EXEMPT_PATHS:
            if path.startswith(exempt):
                return None
        if path.startswith(f'{API_PREFIX}auth/brands/') and (
            path.endswith('/change-plan/') or path.endswith('/checkout/')
        ):
            return None

        _authenticate_token_user(request)

        if request.method in WRITE_METHODS:
            blocked = enforce_brand_write_access(request)
            if blocked:
                return blocked
            return None

        if request.method == 'GET':
            for prefix in SENSITIVE_GET_PREFIXES:
                if path.startswith(prefix):
                    blocked = enforce_sensitive_read_block(request)
                    if blocked:
                        return blocked
                    break
        return None
