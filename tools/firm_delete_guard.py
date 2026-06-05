"""Firma rehberi — çözüm ortağı silme koruması."""

from __future__ import annotations

from django.db.models import Q

from tools.models import MapsScrapedFirm

PARTNER_DELETE_MESSAGE = (
    'Çözüm ortağı kayıtları firma rehberinden silinemez. '
    'Önce Çözüm ağından ortağı kaldırın veya türünü değiştirin.'
)


def is_partner_protected(firm: MapsScrapedFirm) -> bool:
    return (
        firm.firm_kind == MapsScrapedFirm.KIND_PARTNER
        or bool(firm.solution_partner_id)
    )


def partner_protected_filter() -> Q:
    return Q(firm_kind=MapsScrapedFirm.KIND_PARTNER) | Q(solution_partner_id__isnull=False)


def partition_deletable_firms(queryset) -> tuple[list[int], list[dict]]:
    deletable_ids: list[int] = []
    blocked: list[dict] = []
    for firm in queryset:
        if is_partner_protected(firm):
            blocked.append({'id': firm.id, 'name': firm.name})
        else:
            deletable_ids.append(firm.id)
    return deletable_ids, blocked


def format_blocked_names(blocked: list[dict], *, max_names: int = 5) -> str:
    names = [item['name'] for item in blocked[:max_names] if item.get('name')]
    if not names:
        return ''
    suffix = ''
    if len(blocked) > max_names:
        suffix = f' (+{len(blocked) - max_names} kayıt daha)'
    return f'{", ".join(names)}{suffix}'


def delete_firms_response(firms_qs) -> dict:
    deletable_ids, blocked = partition_deletable_firms(firms_qs)
    if blocked and not deletable_ids:
        return {
            'ok': False,
            'error': PARTNER_DELETE_MESSAGE,
            'blocked': len(blocked),
            'blocked_firms': blocked,
        }
    deleted = 0
    if deletable_ids:
        deleted, _ = MapsScrapedFirm.objects.filter(pk__in=deletable_ids).delete()
    payload = {'ok': True, 'deleted': deleted}
    if blocked:
        payload['blocked'] = len(blocked)
        payload['blocked_firms'] = blocked
        payload['warning'] = (
            f'{len(blocked)} çözüm ortağı kaydı korundu. '
            f'{PARTNER_DELETE_MESSAGE}'
        )
    return payload
