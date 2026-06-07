"""Platform denetim kayıtları."""

from __future__ import annotations

from users.models import PlatformAuditLog


def _client_ip(request) -> str | None:
    ip = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip()
    return ip or request.META.get('REMOTE_ADDR') or None


def log_platform_audit(
    request,
    *,
    action: str,
    brand=None,
    target_user=None,
    detail: str = '',
) -> None:
    from users.impersonation import get_real_user

    actor = get_real_user(request)
    if not actor or not actor.is_authenticated:
        return
    PlatformAuditLog.objects.create(
        action=action,
        actor=actor,
        brand=brand,
        target_user=target_user,
        detail=detail[:500],
        ip_address=_client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:500],
    )
