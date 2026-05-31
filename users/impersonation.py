"""Süper admin — hedef kullanıcı rolüyle paneli inceleme (impersonation)."""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model, login
logger = logging.getLogger(__name__)

User = get_user_model()
SESSION_IMPERSONATOR_KEY = '_impersonator_user_id'
AUTH_BACKEND = 'django.contrib.auth.backends.ModelBackend'


class ImpersonationError(Exception):
    pass


def is_impersonating(request) -> bool:
    return bool(request.session.get(SESSION_IMPERSONATOR_KEY))


def get_impersonator_id(request) -> int | None:
    raw = request.session.get(SESSION_IMPERSONATOR_KEY)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def get_impersonator(request):
    """Gerçek süper admin hesabı; impersonation yoksa None."""
    pk = get_impersonator_id(request)
    if not pk:
        return None
    return User.objects.filter(pk=pk, is_active=True, is_superuser=True).first()


def can_impersonate(actor, target, *, already_impersonating: bool = False) -> tuple[bool, str]:
    if not actor or not actor.is_authenticated:
        return False, 'Giriş gerekli.'
    if not actor.is_superuser:
        return False, 'Yalnızca süper admin kullanıcı geçişi yapabilir.'
    if already_impersonating:
        return False, 'Önce mevcut kullanıcı görünümünden çıkın.'
    if target.pk == actor.pk:
        return False, 'Kendi hesabınızla geçiş yapılamaz.'
    if target.is_superuser:
        return False, 'Başka bir süper admin hesabına geçiş yapılamaz.'
    if not target.is_active:
        return False, 'Pasif kullanıcı ile geçiş yapılamaz.'
    return True, ''


def start_impersonation(request, target) -> None:
    actor = request.user
    ok, reason = can_impersonate(
        actor,
        target,
        already_impersonating=is_impersonating(request),
    )
    if not ok:
        raise ImpersonationError(reason)

    login(request, target, backend=AUTH_BACKEND)
    request.session[SESSION_IMPERSONATOR_KEY] = actor.pk
    request.session.modified = True
    logger.info(
        'impersonation_start actor_id=%s target_id=%s target_username=%s',
        actor.pk,
        target.pk,
        target.username,
    )


def stop_impersonation(request):
    """Impersonation oturumunu sonlandırır; süper admin hesabına döner."""
    actor_id = get_impersonator_id(request)
    if not actor_id:
        return None, None

    actor = User.objects.filter(pk=actor_id, is_active=True, is_superuser=True).first()
    previous = request.user
    request.session.pop(SESSION_IMPERSONATOR_KEY, None)

    if actor:
        login(request, actor, backend=AUTH_BACKEND)
        request.session.cycle_key()
        logger.info(
            'impersonation_stop actor_id=%s previous_target_id=%s',
            actor.pk,
            getattr(previous, 'pk', None),
        )
    return actor, previous
