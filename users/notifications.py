"""Kullanıcı bildirimleri — oluşturma ve özet."""

from __future__ import annotations

import logging

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from users.models import UserNotification

logger = logging.getLogger(__name__)

REFRESH_THROTTLE_SECONDS = 300


def notify_user(
    user,
    *,
    title: str,
    body: str = '',
    link: str = '',
    level: str = UserNotification.LEVEL_INFO,
    source: str = UserNotification.SOURCE_SYSTEM,
    dedupe_key: str = '',
) -> UserNotification | None:
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if dedupe_key:
        existing = UserNotification.objects.filter(user=user, dedupe_key=dedupe_key).first()
        if existing:
            existing.title = title
            existing.body = body
            existing.link = link
            existing.level = level
            existing.save(update_fields=['title', 'body', 'link', 'level'])
            return existing
    return UserNotification.objects.create(
        user=user,
        title=title,
        body=body,
        link=link,
        level=level,
        source=source,
        dedupe_key=dedupe_key or '',
    )


def unread_count(user) -> int:
    if not user.is_authenticated:
        return 0
    return UserNotification.objects.filter(user=user, is_read=False).count()


def serialize_notification(n: UserNotification) -> dict:
    return {
        'id': n.id,
        'title': n.title,
        'body': n.body,
        'link': n.link,
        'level': n.level,
        'source': n.source,
        'is_read': n.is_read,
        'created_at': timezone.localtime(n.created_at).isoformat(),
        'created_label': timezone.localtime(n.created_at).strftime('%d.%m.%Y %H:%M'),
    }


def list_notifications(user, *, limit: int = 30) -> list[dict]:
    qs = UserNotification.objects.filter(user=user).order_by('-created_at')[:limit]
    return [serialize_notification(n) for n in qs]


def mark_read(user, notification_id: int) -> bool:
    updated = UserNotification.objects.filter(user=user, pk=notification_id, is_read=False).update(is_read=True)
    return updated > 0


def mark_all_read(user) -> int:
    return UserNotification.objects.filter(user=user, is_read=False).update(is_read=True)


def _clear_dedupe(user, dedupe_key: str) -> None:
    UserNotification.objects.filter(user=user, dedupe_key=dedupe_key).delete()


def refresh_system_notifications(user) -> None:
    """Yetkiye göre özet bildirimler — tekrarlı anahtar ile güncellenir."""
    cache_key = f'notif_refresh:{user.pk}'
    if cache.get(cache_key):
        return
    cache.set(cache_key, 1, REFRESH_THROTTLE_SECONDS)

    from common.permissions import can_manage_payroll
    from core_settings.payroll import build_period_summary, parse_period, period_label

    if can_manage_payroll(user):
        period = parse_period(None)
        dedupe = f'payroll-pending-{period.strftime("%Y-%m")}'
        summary = build_period_summary(period)
        pending = sum(1 for row in summary['rows'] if row.get('can_pay') and not row.get('is_paid'))
        if pending:
            notify_user(
                user,
                title=f'{pending} personel için maaş bekliyor',
                body=f'{period_label(period)} dönemi — maaş sayfasından ödeme yapabilirsiniz.',
                link=reverse('accounting_payroll') + f'?period={period.strftime("%Y-%m")}',
                level=UserNotification.LEVEL_WARNING,
                source=UserNotification.SOURCE_PAYROLL,
                dedupe_key=dedupe,
            )
        else:
            _clear_dedupe(user, dedupe)

    if user.has_any_perm_codename('sales.reports', 'sales.manage'):
        try:
            from sales_leads.receivables import build_receivables_context

            summary = build_receivables_context()
            overdue = summary.get('receivable_overdue_count') or 0
            if overdue:
                notify_user(
                    user,
                    title=f'{overdue} gecikmiş alacak',
                    body='Tahsilat takibi için alacaklar sayfasına gidin.',
                    link=reverse('accounting_receivables') + '?overdue=1',
                    level=UserNotification.LEVEL_WARNING,
                    source=UserNotification.SOURCE_RECEIVABLES,
                    dedupe_key='receivables-overdue',
                )
            else:
                _clear_dedupe(user, 'receivables-overdue')
        except Exception:
            logger.exception('Alacak bildirimi güncellenemedi (user=%s)', user.pk)
