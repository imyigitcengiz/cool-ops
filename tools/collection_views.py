import uuid



from django.shortcuts import get_object_or_404

from django.http import JsonResponse

from django.utils import timezone

from django.views.decorators.http import require_http_methods



from tools.collections import (
    DEFAULT_TEMPLATE,
    add_firm_to_collection,
    add_manual_to_collection,
    add_customer_to_collection,
    get_or_create_default_collection,
    serialize_collection,
)
from customers.models import Customer

from tools.models import MapsScrapedFirm, OutreachCollection, OutreachCollectionMember, WhatsappOutboundMessage

from tools.outreach_memory import has_been_messaged_globally

from tools.phone_utils import is_whatsapp_eligible

from tools.views import _apply_template, _json_body





def _get_collection(pk):

    return get_object_or_404(OutreachCollection, pk=pk)





@require_http_methods(['GET', 'POST'])

def collections_api(request):

    if request.method == 'GET':

        items = [serialize_collection(c) for c in OutreachCollection.objects.all()]

        if not items:

            default = get_or_create_default_collection()

            items = [serialize_collection(default)]

        return JsonResponse({'ok': True, 'collections': items})



    body = _json_body(request) or {}

    name = (body.get('name') or '').strip() or 'Yeni Kampanya'

    col = OutreachCollection.objects.create(

        name=name,

        message_template=(body.get('message_template') or DEFAULT_TEMPLATE).strip(),

        skip_globally_messaged=bool(body.get('skip_globally_messaged', False)),

        allow_repeat_in_campaign=bool(body.get('allow_repeat_in_campaign', True)),

        delay_seconds=int(body.get('delay_seconds') or 4),

    )

    return JsonResponse({'ok': True, 'collection': serialize_collection(col, include_members=True)})





@require_http_methods(['GET', 'PATCH', 'DELETE'])

def collection_detail_api(request, pk):

    col = _get_collection(pk)

    if request.method == 'GET':

        return JsonResponse({'ok': True, 'collection': serialize_collection(col, include_members=True)})



    if request.method == 'DELETE':

        col.delete()

        return JsonResponse({'ok': True})



    body = _json_body(request) or {}

    if 'name' in body:

        col.name = (body.get('name') or col.name).strip()[:120]

    if 'message_template' in body:

        col.message_template = body.get('message_template') or col.message_template

    if 'skip_globally_messaged' in body:

        col.skip_globally_messaged = bool(body.get('skip_globally_messaged'))

    if 'allow_repeat_in_campaign' in body:

        col.allow_repeat_in_campaign = bool(body.get('allow_repeat_in_campaign'))

    if 'delay_seconds' in body:

        col.delay_seconds = max(1, min(int(body.get('delay_seconds') or 4), 30))

    col.save()

    return JsonResponse({'ok': True, 'collection': serialize_collection(col, include_members=True)})





@require_http_methods(['POST'])

def collection_clear_api(request, pk):

    col = _get_collection(pk)

    deleted, _ = col.members.all().delete()

    return JsonResponse({'ok': True, 'removed': deleted})





@require_http_methods(['POST'])

def collection_add_members_api(request, pk):

    col = _get_collection(pk)

    body = _json_body(request) or {}

    firm_ids = body.get('firm_ids') or []
    customer_ids = body.get('customer_ids') or []
    manual = body.get('manual') or []



    added = 0

    skipped = 0

    warnings = []



    for firm_id in firm_ids:

        try:

            firm = MapsScrapedFirm.objects.get(pk=int(firm_id))

        except (MapsScrapedFirm.DoesNotExist, TypeError, ValueError):

            skipped += 1

            continue

        member, reason = add_firm_to_collection(col, firm)

        if member:

            added += 1

        else:

            skipped += 1

            if reason:

                warnings.append(f'{firm.name}: {reason}')

    for customer_id in customer_ids:
        try:
            customer = Customer.objects.get(pk=int(customer_id))
        except (Customer.DoesNotExist, TypeError, ValueError):
            skipped += 1
            continue
        member, reason = add_customer_to_collection(col, customer)
        if member:
            added += 1
        else:
            skipped += 1
            if reason:
                warnings.append(f'{customer.name}: {reason}')

    for entry in manual:

        name = (entry.get('name') or '').strip()

        phone = (entry.get('phone') or '').strip()

        member, reason = add_manual_to_collection(col, name, phone)

        if member:

            added += 1

        else:

            skipped += 1

            if reason:

                warnings.append(f'{name or phone}: {reason}')



    col.save(update_fields=['updated_at'])

    return JsonResponse({

        'ok': True,

        'added': added,

        'skipped': skipped,

        'warnings': warnings[:20],

        'collection': serialize_collection(col, include_members=True),

    })





@require_http_methods(['DELETE', 'PATCH'])
def collection_remove_member_api(request, pk, member_id):
    col = _get_collection(pk)
    member = get_object_or_404(OutreachCollectionMember, collection=col, pk=member_id)
    if request.method == 'PATCH':
        body = _json_body(request) or {}
        if 'custom_message' in body:
            member.custom_message = (body.get('custom_message') or '').strip()
            member.save(update_fields=['custom_message'])
        if 'name' in body:
            member.name = (body.get('name') or member.name).strip()[:255]
            member.save(update_fields=['name'])
        return JsonResponse({'ok': True, 'collection': serialize_collection(col, include_members=True)})
    member.delete()
    return JsonResponse({'ok': True, 'collection': serialize_collection(col, include_members=True)})





def _already_sent_in_collection(collection, phone_norm):

    if collection.allow_repeat_in_campaign:

        return False

    return WhatsappOutboundMessage.objects.filter(

        collection=collection,

        phone_normalized=phone_norm,

        status=WhatsappOutboundMessage.STATUS_SENT,

    ).exists()





def _should_skip_member(col, member) -> str | None:

    phone_norm = member.phone_normalized

    phone_display = member.phone_display or phone_norm



    if not is_whatsapp_eligible(phone_display, phone_norm):

        return 'Sabit hat'



    if col.skip_globally_messaged and has_been_messaged_globally(phone_norm):

        return 'Daha önce mesaj atıldı'



    if _already_sent_in_collection(col, phone_norm):

        return 'Bu kampanyadan daha önce gönderildi'



    return None





def _resolve_member_firm(member):

    if member.firm_id:

        return member.firm

    firm = MapsScrapedFirm.objects.filter(phone_normalized=member.phone_normalized).first()

    if firm:

        member.firm = firm

        member.save(update_fields=['firm'])

    return firm





@require_http_methods(['POST'])

def collection_queue_api(request, pk):

    col = _get_collection(pk)

    body = _json_body(request) or {}

    template = (body.get('template') or col.message_template or DEFAULT_TEMPLATE).strip()

    if not template:

        return JsonResponse({'ok': False, 'error': 'Mesaj şablonu girin.'}, status=400)



    batch_id = body.get('batch_id') or uuid.uuid4().hex



    WhatsappOutboundMessage.objects.filter(

        collection=col,

        status__in=[

            WhatsappOutboundMessage.STATUS_PENDING,

            WhatsappOutboundMessage.STATUS_SENDING,

        ],

    ).update(

        status=WhatsappOutboundMessage.STATUS_SKIPPED,

        error_message='Yeni gönderim başlatıldı',

    )



    WhatsappOutboundMessage.objects.filter(

        batch_id=batch_id,

        status=WhatsappOutboundMessage.STATUS_PENDING,

    ).delete()



    members = col.members.select_related('firm').order_by('id')

    if not members.exists():

        return JsonResponse({'ok': False, 'error': 'Koleksiyon listesi boş.'}, status=400)



    created = 0

    skipped = 0

    skip_reasons = []



    for member in members:

        skip_reason = _should_skip_member(col, member)

        if skip_reason:

            skipped += 1

            skip_reasons.append(f'{member.name or member.phone_normalized}: {skip_reason}')

            continue



        firm = _resolve_member_firm(member)

        phone_norm = member.phone_normalized

        phone_display = member.phone_display or phone_norm



        message = (member.custom_message or '').strip()
        if not message:
            message = _apply_template(
                template, firm, name=member.name, phone=phone_display,
                region=firm.region if firm else '',
            )

        WhatsappOutboundMessage.objects.create(

            collection=col,

            firm=firm,

            recipient_name=member.name or (firm.name if firm else 'Alıcı'),

            phone_normalized=phone_norm,

            phone_display=phone_display,

            message=message,

            batch_id=batch_id,

            source=(

                WhatsappOutboundMessage.SOURCE_SCRAPED

                if firm and firm.place_id

                else WhatsappOutboundMessage.SOURCE_MANUAL

            ),
            send_type=WhatsappOutboundMessage.SEND_CAMPAIGN,

        )

        created += 1



    return JsonResponse({

        'ok': True,

        'batch_id': batch_id,

        'queued': created,

        'skipped': skipped,

        'skip_reasons': skip_reasons[:15],

        'collection_id': col.id,

    })


