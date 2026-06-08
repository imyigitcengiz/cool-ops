"""Abonelik ödemeleri — mock / Stripe / iyzico."""

import base64
import hashlib
import json
import os
import random
import string
import uuid
from datetime import timedelta
from decimal import Decimal
from urllib import error, request as urlrequest

from django.conf import settings
from django.utils import timezone

from core_settings.models import BusinessBrand
from restaurant.compat import get_tenant_profile
from restaurant.models import Invoice, RestaurantProfile
from restaurant.api.plan_limits import PLAN_LIMITS


def get_active_provider():
    preferred = os.environ.get('PAYMENT_PROVIDER', 'auto').lower()
    if preferred == 'mock':
        if not settings.DEBUG:
            raise RuntimeError('Mock ödeme production ortamında kullanılamaz.')
        return 'mock'
    if preferred == 'stripe' and os.environ.get('STRIPE_SECRET_KEY'):
        return 'stripe'
    if preferred == 'iyzico' and os.environ.get('IYZICO_API_KEY') and os.environ.get('IYZICO_SECRET_KEY'):
        return 'iyzico'
    if preferred == 'auto':
        if os.environ.get('STRIPE_SECRET_KEY'):
            return 'stripe'
        if os.environ.get('IYZICO_API_KEY') and os.environ.get('IYZICO_SECRET_KEY'):
            return 'iyzico'
    if settings.DEBUG:
        return 'mock'
    raise RuntimeError(
        'Ödeme sağlayıcısı yapılandırılmamış. STRIPE_SECRET_KEY veya IYZICO anahtarlarını tanımlayın.'
    )


def get_frontend_base_url():
    return os.environ.get('FRONTEND_URL', 'http://localhost:8000/restoran').rstrip('/')


def get_backend_base_url():
    return os.environ.get('BACKEND_URL', 'http://localhost:8000').rstrip('/')


def _generate_invoice_number():
    return f"INV-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


def create_pending_invoice(brand, plan):
    amount = Decimal(str(PLAN_LIMITS.get(plan, PLAN_LIMITS['starter'])['price']))
    Invoice.objects.filter(brand=brand, payment_status='pending').update(payment_status='cancelled')
    return Invoice.objects.create(
        brand=brand,
        invoice_number=_generate_invoice_number(),
        amount=amount,
        plan=plan,
        paid=False,
        payment_status='pending',
        payment_provider=get_active_provider(),
    )


def fulfill_subscription_payment(invoice):
    if invoice.paid:
        return invoice
    brand = invoice.brand
    tenant = get_tenant_profile(brand)
    from common.brand_team import subscription_owner_for_brand
    from common.plan_sync import billing_days_for_restaurant_tier

    owner = subscription_owner_for_brand(brand)
    cycle_days = billing_days_for_restaurant_tier(invoice.plan, owner=owner)

    tenant.plan_tier = invoice.plan
    today = timezone.localdate()
    if tenant.plan_expiry and tenant.plan_expiry >= today:
        tenant.plan_expiry = tenant.plan_expiry + timedelta(days=cycle_days)
    else:
        tenant.plan_expiry = today + timedelta(days=cycle_days)
    tenant.save(update_fields=['plan_tier', 'plan_expiry'])
    brand.is_active = True
    brand.save(update_fields=['is_active'])

    plan_profile_map = {'starter': 'Starter', 'growth': 'Growth', 'enterprise': 'Enterprise'}
    profile_label = plan_profile_map.get(invoice.plan, 'Starter')
    RestaurantProfile.objects.filter(brand=brand).update(active_plan=profile_label)

    invoice.paid = True
    invoice.payment_status = 'paid'
    invoice.paid_at = timezone.now()
    invoice.save(update_fields=['paid', 'payment_status', 'paid_at'])

    from common.plan_sync import sync_owner_plan_from_tier

    owner = subscription_owner_for_brand(brand)
    if owner:
        sync_owner_plan_from_tier(owner, tenant.plan_tier)

    return invoice


def serialize_invoice(invoice):
    return {
        'id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'amount': float(invoice.amount),
        'plan': invoice.plan,
        'created_at': invoice.created_at.isoformat(),
        'paid': invoice.paid,
        'payment_provider': invoice.payment_provider,
        'payment_status': invoice.payment_status,
        'checkout_url': invoice.checkout_url,
        'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None,
    }


def _http_post_json(url, payload, headers):
    data = json.dumps(payload).encode('utf-8')
    req = urlrequest.Request(url, data=data, headers=headers, method='POST')
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'HTTP {exc.code}: {body}') from exc


def _create_stripe_checkout(invoice, brand, user):
    secret = os.environ.get('STRIPE_SECRET_KEY')
    if not secret:
        raise RuntimeError('STRIPE_SECRET_KEY tanımlı değil.')
    frontend = get_frontend_base_url()
    amount_cents = int(invoice.amount * 100)
    plan_label = PLAN_LIMITS.get(invoice.plan, {}).get('label', invoice.plan)
    payload = {
        'mode': 'payment',
        'success_url': f'{frontend}/payment/success?provider=stripe&session_id={{CHECKOUT_SESSION_ID}}',
        'cancel_url': f'{frontend}/payment/cancel?provider=stripe',
        'client_reference_id': str(invoice.id),
        'customer_email': user.email or None,
        'metadata[invoice_id]': str(invoice.id),
        'metadata[brand_id]': str(brand.id),
        'metadata[plan]': invoice.plan,
        'line_items[0][price_data][currency]': 'try',
        'line_items[0][price_data][unit_amount]': str(amount_cents),
        'line_items[0][price_data][product_data][name]': f'Restoran POS — {plan_label} Plan (Aylık)',
        'line_items[0][quantity]': '1',
    }
    form_body = '&'.join(
        f'{k}={urlrequest.quote(str(v))}' for k, v in payload.items() if v is not None
    )
    req = urlrequest.Request(
        'https://api.stripe.com/v1/checkout/sessions',
        data=form_body.encode('utf-8'),
        headers={
            'Authorization': f'Bearer {secret}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST',
    )
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
    except error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'Stripe hatası: {body}') from exc
    invoice.external_id = result['id']
    invoice.checkout_url = result['url']
    invoice.payment_provider = 'stripe'
    invoice.save(update_fields=['external_id', 'checkout_url', 'payment_provider'])
    return result['url']


def _iyzico_auth_header(api_key, secret_key, body_str):
    random_key = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    digest = hashlib.sha256(f'{api_key}{random_key}{secret_key}{body_str}'.encode()).hexdigest()
    token = base64.b64encode(
        f'apiKey:{api_key}&randomKey:{random_key}&signature:{digest}'.encode()
    ).decode()
    return f'IYZWSv2 {token}'


def _create_iyzico_checkout(invoice, brand, user):
    api_key = os.environ.get('IYZICO_API_KEY')
    secret_key = os.environ.get('IYZICO_SECRET_KEY')
    if not api_key or not secret_key:
        raise RuntimeError('IYZICO_API_KEY / IYZICO_SECRET_KEY tanımlı değil.')
    base = os.environ.get('IYZICO_BASE_URL', 'https://sandbox-api.iyzipay.com')
    frontend = get_frontend_base_url()
    backend = get_backend_base_url()
    conversation_id = str(uuid.uuid4())[:36]
    basket_id = f'B{invoice.id}'
    plan_label = PLAN_LIMITS.get(invoice.plan, {}).get('label', invoice.plan)
    buyer_name = user.first_name or user.username
    buyer_surname = user.last_name or 'Kullanici'
    rest_profile = RestaurantProfile.objects.filter(brand=brand).first()
    buyer_phone = (rest_profile.phone if rest_profile and rest_profile.phone else '+905555555555')
    payload = {
        'locale': 'tr',
        'conversationId': conversation_id,
        'price': str(invoice.amount),
        'paidPrice': str(invoice.amount),
        'currency': 'TRY',
        'basketId': basket_id,
        'paymentGroup': 'SUBSCRIPTION',
        'callbackUrl': f'{backend}/restoran/api/payments/iyzico/callback/',
        'enabledInstallments': [1],
        'buyer': {
            'id': str(user.id),
            'name': buyer_name,
            'surname': buyer_surname,
            'gsmNumber': buyer_phone,
            'email': user.email or f'{user.username}@coolops.local',
            'identityNumber': '11111111111',
            'registrationAddress': brand.name,
            'ip': '85.34.78.112',
            'city': 'Istanbul',
            'country': 'Turkey',
        },
        'shippingAddress': {
            'contactName': f'{buyer_name} {buyer_surname}',
            'city': 'Istanbul',
            'country': 'Turkey',
            'address': brand.name,
        },
        'billingAddress': {
            'contactName': f'{buyer_name} {buyer_surname}',
            'city': 'Istanbul',
            'country': 'Turkey',
            'address': brand.name,
        },
        'basketItems': [{
            'id': f'PLAN-{invoice.plan}',
            'name': f'Restoran POS {plan_label} Abonelik',
            'category1': 'SaaS',
            'itemType': 'VIRTUAL',
            'price': str(invoice.amount),
        }],
    }
    body_str = json.dumps(payload, separators=(',', ':'))
    headers = {
        'Content-Type': 'application/json',
        'Authorization': _iyzico_auth_header(api_key, secret_key, body_str),
    }
    result = _http_post_json(f'{base}/payment/iyzipos/checkoutform/initialize/auth/ecom', payload, headers)
    if result.get('status') != 'success':
        raise RuntimeError(result.get('errorMessage') or 'iyzico ödeme başlatılamadı.')
    invoice.external_id = result.get('token') or conversation_id
    invoice.checkout_url = result.get('paymentPageUrl') or result.get('payWithIyzicoPageUrl')
    invoice.payment_provider = 'iyzico'
    invoice.save(update_fields=['external_id', 'checkout_url', 'payment_provider'])
    return invoice.checkout_url


def _create_mock_checkout(invoice):
    fulfill_subscription_payment(invoice)
    invoice.payment_provider = 'mock'
    invoice.checkout_url = None
    invoice.external_id = f'mock-{invoice.id}'
    invoice.save(update_fields=['payment_provider', 'checkout_url', 'external_id'])
    return None


def initiate_checkout(brand, plan, user):
    provider = get_active_provider()
    invoice = create_pending_invoice(brand, plan)
    invoice.payment_provider = provider
    invoice.save(update_fields=['payment_provider'])
    if provider == 'stripe':
        checkout_url = _create_stripe_checkout(invoice, brand, user)
        return invoice, checkout_url, provider
    if provider == 'iyzico':
        checkout_url = _create_iyzico_checkout(invoice, brand, user)
        return invoice, checkout_url, provider
    _create_mock_checkout(invoice)
    return invoice, None, 'mock'


def verify_stripe_session(session_id, user=None):
    secret = os.environ.get('STRIPE_SECRET_KEY')
    if not secret:
        return None, 'Stripe yapılandırılmamış.'
    req = urlrequest.Request(
        f'https://api.stripe.com/v1/checkout/sessions/{session_id}',
        headers={'Authorization': f'Bearer {secret}'},
    )
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            session = json.loads(resp.read().decode('utf-8'))
    except error.HTTPError as exc:
        return None, exc.read().decode('utf-8', errors='replace')
    if session.get('payment_status') != 'paid':
        return None, 'Ödeme henüz tamamlanmadı.'
    invoice_id = session.get('metadata', {}).get('invoice_id') or session.get('client_reference_id')
    if not invoice_id:
        return None, 'Fatura bilgisi bulunamadı.'
    try:
        invoice = Invoice.objects.select_related('brand').get(id=int(invoice_id))
    except (Invoice.DoesNotExist, ValueError, TypeError):
        return None, 'Fatura bulunamadı.'
    if user is not None:
        from restaurant.api.tenant_helpers import user_owns_brand
        from restaurant.compat import get_api_profile
        profile = get_api_profile(user)
        from restaurant.api.security import is_api_superuser
        if not is_api_superuser(user) and not user_owns_brand(user, invoice.brand):
            return None, 'Bu faturayı doğrulama yetkiniz yok.'
    fulfill_subscription_payment(invoice)
    if not invoice.external_id:
        invoice.external_id = session_id
        invoice.save(update_fields=['external_id'])
    return invoice, None


def verify_iyzico_token(token):
    api_key = os.environ.get('IYZICO_API_KEY')
    secret_key = os.environ.get('IYZICO_SECRET_KEY')
    if not api_key or not secret_key:
        return None, 'iyzico yapılandırılmamış.'
    base = os.environ.get('IYZICO_BASE_URL', 'https://sandbox-api.iyzipay.com')
    payload = {'locale': 'tr', 'token': token}
    body_str = json.dumps(payload, separators=(',', ':'))
    headers = {
        'Content-Type': 'application/json',
        'Authorization': _iyzico_auth_header(api_key, secret_key, body_str),
    }
    result = _http_post_json(f'{base}/payment/iyzipos/checkoutform/auth/ecom/detail', payload, headers)
    if result.get('paymentStatus') != 'SUCCESS':
        return None, result.get('errorMessage') or 'Ödeme başarısız.'
    basket_id = result.get('basketId', '')
    if not basket_id.startswith('B'):
        return None, 'Sepet bilgisi geçersiz.'
    try:
        invoice_id = int(basket_id[1:])
        invoice = Invoice.objects.select_related('brand').get(id=invoice_id)
    except (Invoice.DoesNotExist, ValueError):
        return None, 'Fatura bulunamadı.'
    fulfill_subscription_payment(invoice)
    invoice.external_id = token
    invoice.save(update_fields=['external_id'])
    return invoice, None
