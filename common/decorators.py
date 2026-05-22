from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from common.middleware import _is_api_request


def _deny(request, message='Bu işlem için yetkiniz yok.'):
    if _is_api_request(request):
        return JsonResponse({'ok': False, 'error': message}, status=403)
    messages.error(request, message)
    return redirect('home')


def permission_required(*codenames, any_perm=False):
    """View fonksiyonları için izin kontrolü."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect('login')
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            codes = [c for c in codenames if c]
            if not codes:
                return view_func(request, *args, **kwargs)
            allowed = (
                user.has_any_perm_codename(*codes)
                if any_perm
                else all(user.has_perm_codename(c) for c in codes)
            )
            if not allowed:
                return _deny(request)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
