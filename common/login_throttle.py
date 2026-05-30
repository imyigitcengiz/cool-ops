"""Basit giriş denemesi sınırlayıcı (brute-force koruması)."""

from __future__ import annotations

import hashlib

from django.core.cache import cache

LOGIN_ATTEMPT_LIMIT = 10
LOGIN_ATTEMPT_WINDOW = 900  # 15 dk
LOGIN_LOCKOUT_SECONDS = 900


def _cache_key(identifier: str) -> str:
    digest = hashlib.sha256(identifier.encode('utf-8')).hexdigest()[:32]
    return f'login_attempts:{digest}'


def is_login_blocked(request) -> bool:
    ip = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip()
    if not ip:
        ip = request.META.get('REMOTE_ADDR') or 'unknown'
    username = (request.POST.get('username') or request.GET.get('username') or '').strip().lower()
    key = _cache_key(f'{ip}:{username}')
    return int(cache.get(key, 0) or 0) >= LOGIN_ATTEMPT_LIMIT


def register_failed_login(request) -> None:
    ip = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip()
    if not ip:
        ip = request.META.get('REMOTE_ADDR') or 'unknown'
    username = (request.POST.get('username') or '').strip().lower()
    key = _cache_key(f'{ip}:{username}')
    attempts = int(cache.get(key, 0) or 0) + 1
    cache.set(key, attempts, LOGIN_ATTEMPT_WINDOW)


def clear_login_attempts(request, username: str = '') -> None:
    ip = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip()
    if not ip:
        ip = request.META.get('REMOTE_ADDR') or 'unknown'
    user = (username or request.POST.get('username') or '').strip().lower()
    cache.delete(_cache_key(f'{ip}:{user}'))
