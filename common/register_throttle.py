"""Kayıt (üyelik) denemesi sınırlayıcı — IP bazlı brute-force koruması."""

from __future__ import annotations

import hashlib

from django.core.cache import cache

REGISTER_ATTEMPT_LIMIT = 5
REGISTER_ATTEMPT_WINDOW = 3600  # 1 saat


def _cache_key(ip: str) -> str:
    digest = hashlib.sha256(ip.encode('utf-8')).hexdigest()[:32]
    return f'register_attempts:{digest}'


def _client_ip(request) -> str:
    ip = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip()
    return ip or request.META.get('REMOTE_ADDR') or 'unknown'


def is_register_blocked(request) -> bool:
    return int(cache.get(_cache_key(_client_ip(request)), 0) or 0) >= REGISTER_ATTEMPT_LIMIT


def register_attempt(request) -> None:
    key = _cache_key(_client_ip(request))
    attempts = int(cache.get(key, 0) or 0) + 1
    cache.set(key, attempts, REGISTER_ATTEMPT_WINDOW)
