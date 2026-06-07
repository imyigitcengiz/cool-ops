"""Impersonate işlemlerinin kalıcı denetim kaydı."""

from __future__ import annotations

from users.models import ImpersonationAudit


def _client_ip(request) -> str | None:
    ip = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip()
    return ip or request.META.get('REMOTE_ADDR') or None


def log_impersonation_audit(request, *, action: str, actor, target) -> None:
    ImpersonationAudit.objects.create(
        action=action,
        actor=actor,
        target=target,
        ip_address=_client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:500],
    )
