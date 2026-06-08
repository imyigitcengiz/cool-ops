import json
import logging
import os

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core_settings.models import BusinessBrand
from restaurant.compat import get_api_profile
from restaurant.api.auth_views import _serialize_brand, _serialize_user
from restaurant.api.payment_service import (
    get_active_provider,
    initiate_checkout,
    serialize_invoice,
    verify_iyzico_token,
    verify_stripe_session,
)
from restaurant.api.security import is_api_superuser

logger = logging.getLogger(__name__)


def _can_checkout(request, brand_id):
    profile = get_api_profile(request.user, request)
    if is_api_superuser(request.user):
        return profile, BusinessBrand.objects.filter(id=brand_id).first(), None
    if profile.role != 'store_owner' or not profile.brand or profile.brand.id != brand_id:
        return None, None, Response({'error': 'Plan ödemesi yalnızca kurum yöneticisine aittir.'}, status=status.HTTP_403_FORBIDDEN)
    return profile, profile.brand, None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_init_view(request, brand_id):
    profile, brand, err = _can_checkout(request, brand_id)
    if err:
        return err
    if not brand:
        return Response({'error': 'Marka bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    plan = request.data.get('plan', 'starter')
    if plan not in ('starter', 'growth', 'enterprise'):
        return Response({'error': 'Geçersiz plan.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        invoice, checkout_url, provider = initiate_checkout(brand, plan, request.user)
    except RuntimeError:
        return Response({'error': 'Ödeme servisi yapılandırılmamış.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response({
        'invoice': serialize_invoice(invoice),
        'checkout_url': checkout_url,
        'provider': provider,
        'brand': _serialize_brand(brand),
        'user': _serialize_user(request.user, profile, request),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_providers_view(request):
    try:
        provider = get_active_provider()
    except RuntimeError:
        return Response({'error': 'Ödeme servisi yapılandırılmamış.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response({'provider': provider, 'providers': ['mock', 'stripe', 'iyzico']})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stripe_verify_view(request):
    session_id = request.query_params.get('session_id')
    if not session_id:
        return Response({'error': 'session_id gerekli.'}, status=status.HTTP_400_BAD_REQUEST)
    invoice, err = verify_stripe_session(session_id, request.user)
    if err:
        return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'invoice': serialize_invoice(invoice), 'message': 'Ödeme doğrulandı.'})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook_view(request):
    secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '').strip()
    if not secret:
        logger.warning('Stripe webhook secret missing — event ignored')
        return HttpResponse(status=200)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '').strip()
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError:
        return HttpResponse(status=400)
    except Exception:
        logger.exception('Stripe webhook verification failed')
        return HttpResponse(status=400)

    if event.get('type') == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session.get('id')
        if session_id:
            verify_stripe_session(session_id, user=None)
    return HttpResponse(status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def iyzico_callback_view(request):
    token = request.data.get('token') or request.POST.get('token')
    if not token:
        try:
            body = json.loads(request.body.decode('utf-8'))
            token = body.get('token')
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    if not token:
        return Response({'error': 'Token gerekli.'}, status=status.HTTP_400_BAD_REQUEST)
    invoice, err = verify_iyzico_token(token)
    if err:
        return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
    if invoice.status == 'paid':
        return Response({'invoice': serialize_invoice(invoice), 'message': 'Ödeme zaten işlendi.'})
    return Response({'invoice': serialize_invoice(invoice), 'message': 'Ödeme doğrulandı.'})
