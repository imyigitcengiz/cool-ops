"""Firma hafızası ve mesaj geçmişi için ortak mantık."""

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from tools.models import MapsScrapedFirm, OutreachCollectionMember, WhatsappOutboundMessage


def get_sent_count(phone_normalized: str) -> int:
    """Hafızadaki firmanın mesaj sayısı — hafıza silinince sıfırlanır."""
    if not phone_normalized:
        return 0
    firm = MapsScrapedFirm.objects.filter(phone_normalized=phone_normalized).only('messages_sent_count').first()
    return firm.messages_sent_count if firm else 0


def has_been_messaged_globally(phone_normalized: str) -> bool:
    """Hafızada kayıtlı ve daha önce mesaj atılmış mı."""
    return get_sent_count(phone_normalized) > 0


def get_last_message_at(phone_normalized: str):
    if not phone_normalized:
        return None
    firm = MapsScrapedFirm.objects.filter(phone_normalized=phone_normalized).only('last_message_at').first()
    return firm.last_message_at if firm else None


def sync_firm_message_stats(firm: MapsScrapedFirm) -> MapsScrapedFirm:
    if not firm.phone_normalized:
        return firm
    sent_count = WhatsappOutboundMessage.objects.filter(
        phone_normalized=firm.phone_normalized,
        status=WhatsappOutboundMessage.STATUS_SENT,
    ).count()
    last_sent = (
        WhatsappOutboundMessage.objects.filter(
            phone_normalized=firm.phone_normalized,
            status=WhatsappOutboundMessage.STATUS_SENT,
        )
        .aggregate(last=Max('sent_at'))
        .get('last')
    )
    firm.messages_sent_count = max(firm.messages_sent_count or 0, sent_count)
    if last_sent and (not firm.last_message_at or last_sent > firm.last_message_at):
        firm.last_message_at = last_sent
    firm.save(update_fields=['messages_sent_count', 'last_message_at'])
    return firm


def ensure_firm_record(*, name: str, phone_raw: str, phone_normalized: str, notes: str = '') -> MapsScrapedFirm:
    firm = MapsScrapedFirm.objects.filter(phone_normalized=phone_normalized).first()
    if firm:
        updates = {}
        if phone_raw and not firm.phone:
            updates['phone'] = phone_raw
        if name and firm.name in ('', 'İsimsiz', 'Manuel', 'Manuel kayıt', 'Alıcı'):
            updates['name'] = name
        if notes and not firm.notes:
            updates['notes'] = notes
        if updates:
            for key, val in updates.items():
                setattr(firm, key, val)
            firm.save(update_fields=list(updates.keys()))
        return sync_firm_message_stats(firm)

    firm = MapsScrapedFirm.objects.create(
        name=name or 'Manuel',
        phone=phone_raw or phone_normalized,
        phone_normalized=phone_normalized,
        notes=notes or 'Manuel eklendi',
    )
    return firm


@transaction.atomic
def merge_firm_records(primary: MapsScrapedFirm, secondary: MapsScrapedFirm) -> MapsScrapedFirm:
    if primary.pk == secondary.pk:
        return primary

    for field in ('address', 'phone', 'phone_normalized', 'website', 'rating', 'reviews', 'maps_url', 'lat', 'lng', 'place_id', 'notes'):
        primary_val = getattr(primary, field, '') or ''
        secondary_val = getattr(secondary, field, '') or ''
        if not primary_val and secondary_val:
            setattr(primary, field, secondary_val)

    primary.messages_sent_count = max(primary.messages_sent_count or 0, secondary.messages_sent_count or 0)
    if secondary.last_message_at and (not primary.last_message_at or secondary.last_message_at > primary.last_message_at):
        primary.last_message_at = secondary.last_message_at
    primary.last_scraped_at = timezone.now()
    primary.save()

    OutreachCollectionMember.objects.filter(firm=secondary).update(firm=primary)
    WhatsappOutboundMessage.objects.filter(firm=secondary).update(firm=primary)

    secondary.delete()
    return sync_firm_message_stats(primary)


def resolve_firm_for_send(message: WhatsappOutboundMessage) -> MapsScrapedFirm | None:
    if message.firm_id:
        return sync_firm_message_stats(message.firm)

    phone_norm = message.phone_normalized
    if not phone_norm:
        return None

    firm = MapsScrapedFirm.objects.filter(phone_normalized=phone_norm).first()
    if not firm:
        firm = MapsScrapedFirm.objects.create(
            name=message.recipient_name or 'Manuel',
            phone=message.phone_display or phone_norm,
            phone_normalized=phone_norm,
            notes='WhatsApp gönderimi ile oluşturuldu',
        )
        message.firm = firm
        message.save(update_fields=['firm'])
    return sync_firm_message_stats(firm)


def messaged_firm_count() -> int:
    """Hafızada olup en az bir kez mesaj gönderilmiş firma sayısı."""
    return MapsScrapedFirm.objects.filter(messages_sent_count__gt=0).count()


def memory_stats() -> dict:
    return {
        'memory_total': MapsScrapedFirm.objects.count(),
        'messaged_count': messaged_firm_count(),
    }
