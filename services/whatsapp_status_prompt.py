from __future__ import annotations

from core_settings.models import StatusOption, WhatsAppTemplate
from tools.whatsapp_scenarios import (
    apply_template_variables,
    build_customer_context,
    build_sales_lead_context,
    build_service_context,
    matching_active_templates_for_event,
    matching_templates_for_event,
)


def _status_values(status_id, status_name=None):
    values = []
    if status_id:
        values.append(str(status_id))
    if status_name:
        values.append(status_name)
    return values


def _templates_payload(templates, context):
    return [
        {
            'id': template.id,
            'title': template.title,
            'message': apply_template_variables(template.message, context),
        }
        for template in templates
    ]


def _base_prompt(*, prompt_type, scenario, phone, customer_name, templates, subtitle, **extra):
    if not templates:
        return None
    payload = {
        'prompt_type': prompt_type,
        'scenario': scenario,
        'phone': phone or '',
        'customer_name': customer_name or '-',
        'subtitle': subtitle,
        'templates': _templates_payload(templates, extra.pop('_context')),
    }
    payload.update(extra)
    return payload


def dispatch_confirmed_scenario(
    scenario,
    *,
    phone_raw: str,
    context: dict,
    customer_id=None,
    template_ids=None,
    event_from_values=None,
    event_to_values=None,
):
    templates = matching_templates_for_event(
        scenario,
        event_from_values=event_from_values,
        event_to_values=event_to_values,
    )
    if template_ids is not None:
        allowed = {int(x) for x in template_ids if str(x).isdigit()}
        templates = [t for t in templates if t.id in allowed]

    results = []
    for template in templates:
        from tools.whatsapp_scenarios import _send_template

        outbound, err = _send_template(
            template,
            phone_raw=phone_raw,
            context=context,
            customer_id=customer_id,
        )
        results.append({
            'template_id': template.id,
            'title': template.title,
            'ok': err is None,
            'error': err,
            'message_id': outbound.id if outbound else None,
        })
    return results


def build_whatsapp_status_change_preview(
    service,
    *,
    prev_status_id,
    prev_status_name=None,
    new_status_id,
    new_status_name,
):
    if not prev_status_id or int(prev_status_id) == int(new_status_id):
        return None

    old_name = prev_status_name
    if not old_name and prev_status_id:
        old_status = StatusOption.objects.filter(pk=prev_status_id).first()
        old_name = old_status.name if old_status else None

    from_values = _status_values(prev_status_id, old_name)
    to_values = _status_values(new_status_id, new_status_name)

    templates = matching_active_templates_for_event(
        WhatsAppTemplate.SCENARIO_SERVICE_STATUS,
        event_from_values=from_values,
        event_to_values=to_values,
    )
    if not templates:
        return None

    ctx = build_service_context(service, old_status_name=old_name or '-')
    ctx['yeni_durum'] = new_status_name or '-'
    ctx['status'] = new_status_name or '-'
    ctx['durum'] = new_status_name or '-'

    return _base_prompt(
        prompt_type='status_change',
        scenario=WhatsAppTemplate.SCENARIO_SERVICE_STATUS,
        phone=service.customer.phone if service.customer_id else '',
        customer_name=service.customer.name if service.customer_id else '-',
        templates=templates,
        subtitle=f'#{service.id} · {service.customer.name if service.customer_id else "-"} · {old_name or "—"} → {new_status_name or "—"}',
        _context=ctx,
        service_id=service.id,
        from_label=old_name or '—',
        to_label=new_status_name or '—',
        prev_status_id=prev_status_id,
        prev_status_name=old_name or '',
        new_status_id=new_status_id,
        new_status_name=new_status_name or '',
    )


def build_whatsapp_status_change_prompt(service, prev_status_id, prev_status_name=None):
    if not prev_status_id or prev_status_id == service.status_id:
        return None
    return build_whatsapp_status_change_preview(
        service,
        prev_status_id=prev_status_id,
        prev_status_name=prev_status_name,
        new_status_id=service.status_id,
        new_status_name=service.status.name if service.status_id else '',
    )


def build_whatsapp_service_created_prompt(service):
    to_values = _status_values(
        service.status_id,
        service.status.name if service.status_id else None,
    )
    templates = matching_templates_for_event(
        WhatsAppTemplate.SCENARIO_SERVICE_CREATED,
        event_to_values=to_values,
    )
    if not templates:
        return None

    ctx = build_service_context(service)
    status_label = service.status.name if service.status_id else '—'
    return _base_prompt(
        prompt_type='service_created',
        scenario=WhatsAppTemplate.SCENARIO_SERVICE_CREATED,
        phone=service.customer.phone if service.customer_id else '',
        customer_name=service.customer.name if service.customer_id else '-',
        templates=templates,
        subtitle=f'#{service.id} · {service.customer.name if service.customer_id else "-"} · Yeni servis · {status_label}',
        _context=ctx,
        service_id=service.id,
        event_to_values=to_values,
    )


def build_whatsapp_customer_created_prompt(customer):
    templates = matching_templates_for_event(
        WhatsAppTemplate.SCENARIO_CUSTOMER_CREATED,
    )
    if not templates:
        return None

    ctx = build_customer_context(customer)
    return _base_prompt(
        prompt_type='customer_created',
        scenario=WhatsAppTemplate.SCENARIO_CUSTOMER_CREATED,
        phone=customer.phone or '',
        customer_name=customer.name,
        templates=templates,
        subtitle=f'{customer.name} · Yeni müşteri',
        _context=ctx,
        customer_id=customer.id,
    )


def build_whatsapp_sales_created_prompt(lead):
    to_values = [lead.status]
    templates = matching_templates_for_event(
        WhatsAppTemplate.SCENARIO_SALES_LEAD_CREATED,
        event_to_values=to_values,
    )
    if not templates:
        return None

    ctx = build_sales_lead_context(lead)
    status_choices = dict(lead.STATUS_CHOICES)
    status_label = status_choices.get(lead.status, lead.status)
    return _base_prompt(
        prompt_type='sales_created',
        scenario=WhatsAppTemplate.SCENARIO_SALES_LEAD_CREATED,
        phone=lead.customer.phone if lead.customer_id else '',
        customer_name=lead.customer.name if lead.customer_id else '-',
        templates=templates,
        subtitle=f'{lead.customer.name if lead.customer_id else "-"} · Yeni satış · {status_label}',
        _context=ctx,
        sales_lead_id=lead.id,
        event_to_values=to_values,
    )


def build_whatsapp_sales_status_prompt(lead, prev_status):
    if not prev_status or prev_status == lead.status:
        return None

    templates = matching_templates_for_event(
        WhatsAppTemplate.SCENARIO_SALES_LEAD_STATUS,
        event_from_values=[prev_status],
        event_to_values=[lead.status],
    )
    if not templates:
        return None

    ctx = build_sales_lead_context(lead, old_status_code=prev_status)
    status_choices = dict(lead.STATUS_CHOICES)
    old_label = status_choices.get(prev_status, prev_status)
    new_label = status_choices.get(lead.status, lead.status)
    return _base_prompt(
        prompt_type='sales_status',
        scenario=WhatsAppTemplate.SCENARIO_SALES_LEAD_STATUS,
        phone=lead.customer.phone if lead.customer_id else '',
        customer_name=lead.customer.name if lead.customer_id else '-',
        templates=templates,
        subtitle=f'{lead.customer.name if lead.customer_id else "-"} · {old_label} → {new_label}',
        _context=ctx,
        sales_lead_id=lead.id,
        prev_status=prev_status,
        event_from_values=[prev_status],
        event_to_values=[lead.status],
    )


def dispatch_confirmed_status_whatsapp(service, *, prev_status_id, prev_status_name=None, template_ids=None):
    old_status = StatusOption.objects.filter(pk=prev_status_id).first() if prev_status_id else None
    old_name = prev_status_name or (old_status.name if old_status else None)
    from_values = _status_values(prev_status_id, old_name)
    to_values = _status_values(
        service.status_id,
        service.status.name if service.status_id else None,
    )
    ctx = build_service_context(service, old_status_name=old_name or '-')
    phone = service.customer.phone or '' if service.customer_id else ''
    return dispatch_confirmed_scenario(
        WhatsAppTemplate.SCENARIO_SERVICE_STATUS,
        phone_raw=phone,
        context=ctx,
        customer_id=service.customer_id,
        template_ids=template_ids,
        event_from_values=from_values,
        event_to_values=to_values,
    )


def queue_whatsapp_status_prompts(request, prompts):
    if not prompts:
        return
    existing = request.session.get('whatsapp_status_prompt_queue') or []
    if isinstance(prompts, dict):
        prompts = [prompts]
    request.session['whatsapp_status_prompt_queue'] = existing + prompts
    request.session.modified = True


def peek_whatsapp_status_prompt_queue(request):
    queue = request.session.get('whatsapp_status_prompt_queue') or []
    return list(queue) if isinstance(queue, list) else []


def pop_whatsapp_status_prompt_queue(request):
    queue = request.session.pop('whatsapp_status_prompt_queue', []) or []
    request.session.modified = True
    return queue if isinstance(queue, list) else []
