"""Restoran POS API kimlik doğrulama — KobiHub oturumu + DRF token."""

from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core_settings.models import BrandMembership, BusinessBrand
from restaurant.compat import (
    ensure_restaurant_tenant,
    get_api_profile,
    get_tenant_profile,
    serialize_brand_for_api,
)
from common.brand_team import subscription_owner_for_brand
from common.plan_sync import plan_trial_days
from restaurant.api.plan_limits import (
    PLAN_LIMITS,
    brand_plan,
    get_brand_usage,
    get_plan_status,
    check_limit,
)
from restaurant.api.security import is_api_superuser, issue_user_token
from restaurant.api.throttling import LoginRateThrottle, RegisterRateThrottle
from restaurant.api.tenant_helpers import validate_role_assignment
from restaurant.models import AuditLog, Branch, Invoice

User = get_user_model()

ROLE_LABELS = {
    'super_admin': 'Süper Yönetici',
    'store_owner': 'Kurum Yöneticisi',
    'manager': 'Operasyon Müdürü',
    'waiter': 'Servis Sorumlusu',
    'cashier': 'Finans Sorumlusu',
    'kitchen': 'Üretim Sorumlusu',
}

PLAN_CHOICES = ('starter', 'growth', 'enterprise')


def _brand_owner(brand):
    mem = BrandMembership.objects.filter(
        brand=brand,
        role=BrandMembership.ROLE_OWNER,
    ).select_related('user').first()
    return mem.user if mem else None


def _serialize_brand_brief(brand):
    if not brand:
        return None
    tenant = get_tenant_profile(brand)
    plan = tenant.plan_tier
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['starter'])
    return {
        'id': brand.id,
        'name': brand.name,
        'slug': brand.slug,
        'plan': plan,
        'plan_display': limits['label'],
        'plan_expiry': tenant.plan_expiry.isoformat() if tenant.plan_expiry else None,
        'is_active': brand.is_active,
        'plan_status': get_plan_status(brand),
        'limits': {'branches': limits['branches'], 'staff': limits['staff']},
        'usage': get_brand_usage(brand),
    }


def _serialize_user(user, profile, request=None):
    brand_data = _serialize_brand_brief(profile.brand) if profile.brand else None
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined.isoformat(),
        'role': profile.role,
        'role_display': ROLE_LABELS.get(profile.role, profile.role),
        'phone': profile.phone or '',
        'avatar': profile.avatar.url if profile.avatar else None,
        'brand': brand_data,
    }


def _serialize_brand(brand):
    owner = _brand_owner(brand)
    tenant = get_tenant_profile(brand)
    return {
        'id': brand.id,
        'name': brand.name,
        'slug': brand.slug,
        'plan': tenant.plan_tier,
        'plan_display': PLAN_LIMITS.get(tenant.plan_tier, {}).get('label', tenant.plan_tier),
        'is_active': brand.is_active,
        'plan_expiry': tenant.plan_expiry.isoformat() if tenant.plan_expiry else None,
        'created_at': brand.pk and str(brand.pk),
        'owner': {
            'id': owner.id,
            'username': owner.username,
            'email': owner.email,
            'first_name': owner.first_name,
            'last_name': owner.last_name,
        } if owner else None,
        'member_count': BrandMembership.objects.filter(brand=brand).count(),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_bridge_view(request):
    """Django oturumundan SPA token üretir."""
    from users.impersonation import get_impersonator, is_impersonating

    profile = get_api_profile(request.user, request)
    token, _ = Token.objects.get_or_create(user=request.user)
    impersonator = get_impersonator(request)
    return Response({
        'token': token.key,
        'user': _serialize_user(request.user, profile, request),
        'impersonating': is_impersonating(request),
        'real_user_is_superuser': bool(impersonator and impersonator.is_superuser),
        'inspect_actor': impersonator.username if impersonator else None,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    if not username or not password:
        return Response({'error': 'Kullanıcı adı ve şifre gereklidir.'}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if user is None:
        return Response({'error': 'Geçersiz kullanıcı adı veya şifre.'}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return Response({'error': 'Bu hesap devre dışı bırakılmış.'}, status=status.HTTP_403_FORBIDDEN)
    profile = get_api_profile(user, request)
    if not is_api_superuser(user) and profile.brand and not profile.brand.is_active:
        return Response({
            'error': 'Marka hesabı devre dışı. Destek ile iletişime geçin veya planınızı yenileyin.',
            'code': 'brand_inactive',
        }, status=status.HTTP_403_FORBIDDEN)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': _serialize_user(user, profile, request)})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def public_register_view(request):
    return Response({
        'error': 'Kayıt yalnızca ana platform üzerinden yapılır.',
        'register_url': '/kayit/?vertical=restaurant',
        'code': 'use_platform_register',
    }, status=status.HTTP_410_GONE)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'message': 'Başarıyla çıkış yapıldı.'})


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    profile = get_api_profile(user, request)
    if request.method == 'GET':
        return Response({'user': _serialize_user(user, profile, request)})
    data = request.data
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        user.email = data['email']
    if 'new_password' in data and data['new_password']:
        old_password = data.get('old_password', '')
        if not user.check_password(old_password):
            return Response({'error': 'Mevcut şifre yanlış.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data['new_password'])
    user.save()
    if 'phone' in data:
        profile.phone = data['phone']
    if 'role' in data:
        caller = get_api_profile(request.user, request)
        if is_api_superuser(request.user):
            profile.role = data['role']
    if 'avatar' in request.FILES:
        profile.avatar = request.FILES['avatar']
    profile.save()
    return Response({'user': _serialize_user(user, profile, request)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_view(request):
    caller = get_api_profile(request.user, request)
    if not is_api_superuser(request.user) and caller.role != 'store_owner':
        return Response({'error': 'Yalnızca yöneticiler yeni kullanıcı oluşturabilir.'}, status=status.HTTP_403_FORBIDDEN)
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    if not username or not password:
        return Response({'error': 'Kullanıcı adı ve şifre gereklidir.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Bu kullanıcı adı zaten kullanılıyor.'}, status=status.HTTP_400_BAD_REQUEST)
    if caller.role == 'store_owner' and caller.brand:
        ok, err = check_limit(caller.brand, 'staff')
        if not ok:
            return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
    role = request.data.get('role', 'waiter')
    ok, role_err = validate_role_assignment(request.user, caller.role, role)
    if not ok:
        return Response({'error': role_err}, status=status.HTTP_403_FORBIDDEN)
    user = User.objects.create_user(
        username=username,
        password=password,
        email=request.data.get('email', '').strip(),
        first_name=request.data.get('first_name', '').strip(),
        last_name=request.data.get('last_name', '').strip(),
    )
    profile = get_api_profile(user, request)
    profile.role = role
    profile.phone = request.data.get('phone', '').strip()
    if is_api_superuser(request.user):
        brand_id = request.data.get('brand_id')
        if brand_id:
            try:
                profile.brand = BusinessBrand.objects.get(id=brand_id)
            except BusinessBrand.DoesNotExist:
                pass
    else:
        profile.brand = caller.brand
    profile.save()
    if profile.brand:
        BrandMembership.objects.get_or_create(user=user, brand=profile.brand, defaults={'role': 'member'})
    return Response({'user': _serialize_user(user, profile, request)}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list_view(request):
    caller = get_api_profile(request.user, request)
    if is_api_superuser(request.user):
        users = User.objects.filter(is_superuser=False).order_by('-date_joined')[:200]
    elif caller.role in ('store_owner', 'manager'):
        if not caller.brand:
            return Response([])
        user_ids = BrandMembership.objects.filter(brand=caller.brand).values_list('user_id', flat=True)
        users = User.objects.filter(id__in=user_ids).order_by('-date_joined')
    else:
        return Response({'error': 'Yetkisiz erişim.'}, status=status.HTTP_403_FORBIDDEN)
    return Response([_serialize_user(u, get_api_profile(u, request), request) for u in users])


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_detail_view(request, user_id):
    caller = get_api_profile(request.user, request)
    if not is_api_superuser(request.user) and caller.role != 'store_owner':
        return Response({'error': 'Yetkisiz erişim.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Kullanıcı bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    target_profile = get_api_profile(target_user, request)
    if not is_api_superuser(request.user) and target_profile.brand != caller.brand:
        return Response({'error': 'Bu kullanıcıyı yönetme yetkiniz yok.'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'DELETE':
        if target_user.id == request.user.id:
            return Response({'error': 'Kendinizi silemezsiniz.'}, status=status.HTTP_400_BAD_REQUEST)
        target_user.delete()
        return Response({'message': 'Kullanıcı silindi.'})
    data = request.data
    if 'first_name' in data:
        target_user.first_name = data['first_name']
    if 'last_name' in data:
        target_user.last_name = data['last_name']
    if 'email' in data:
        target_user.email = data['email']
    if 'is_active' in data:
        target_user.is_active = data['is_active']
    if 'password' in data and data['password']:
        target_user.set_password(data['password'])
    target_user.save()
    if 'role' in data:
        ok, role_err = validate_role_assignment(request.user, caller.role, data['role'])
        if not ok:
            return Response({'error': role_err}, status=status.HTTP_403_FORBIDDEN)
        target_profile.role = data['role']
    if 'phone' in data:
        target_profile.phone = data['phone']
    target_profile.save()
    return Response({'user': _serialize_user(target_user, target_profile, request)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def impersonate_view(request, user_id):
    caller = get_api_profile(request.user, request)
    if not is_api_superuser(request.user):
        return Response({'error': 'Yalnızca platform süper yöneticisi bu işlemi yapabilir.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Kullanıcı bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    target_profile = get_api_profile(target_user, request)
    if target_profile.role != 'store_owner':
        return Response({'error': 'Yalnızca mağaza sahipleri olarak giriş yapılabilir.'}, status=status.HTTP_403_FORBIDDEN)
    token = issue_user_token(target_user)
    AuditLog.objects.create(
        actor=request.user,
        target_user=target_user,
        action='impersonate',
        metadata={'target_role': target_profile.role},
    )
    return Response({
        'token': token.key,
        'user': _serialize_user(target_user, target_profile, request),
        'impersonated': True,
        'yonetim_url': '/yonetim/',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def brand_list_view(request):
    caller = get_api_profile(request.user, request)
    if not is_api_superuser(request.user):
        return Response({'error': 'Yetkisiz erişim.'}, status=status.HTTP_403_FORBIDDEN)
    brands = BusinessBrand.objects.filter(
        panel_kind=BusinessBrand.PANEL_HQ,
        restaurant_tenant__isnull=False,
    ).order_by('-pk')
    return Response([_serialize_brand(b) for b in brands])


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def brand_detail_view(request, brand_id):
    caller = get_api_profile(request.user, request)
    if not is_api_superuser(request.user):
        return Response({'error': 'Yetkisiz erişim.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        brand = BusinessBrand.objects.get(id=brand_id)
    except BusinessBrand.DoesNotExist:
        return Response({'error': 'Marka bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        brand.delete()
        return Response({'message': 'Marka silindi.'})
    data = request.data
    tenant = get_tenant_profile(brand)
    if 'name' in data:
        brand.name = data['name']
    if 'plan' in data and data['plan'] in PLAN_CHOICES:
        tenant.plan_tier = data['plan']
        tenant.save(update_fields=['plan_tier'])
    if 'is_active' in data:
        brand.is_active = data['is_active']
    if 'plan_expiry' in data:
        tenant.plan_expiry = data['plan_expiry'] or None
        tenant.save(update_fields=['plan_expiry'])
    brand.save()
    return Response({'brand': _serialize_brand(brand)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def brand_enter_view(request, brand_id):
    caller = get_api_profile(request.user, request)
    if not is_api_superuser(request.user):
        return Response({'error': 'Yetkisiz erişim.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        brand = BusinessBrand.objects.get(id=brand_id)
    except BusinessBrand.DoesNotExist:
        return Response({'error': 'Marka bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    owner = _brand_owner(brand)
    if not owner:
        return Response({'error': 'Bu markanın tanımlı bir sahibi yok.'}, status=status.HTTP_400_BAD_REQUEST)
    token = issue_user_token(owner)
    owner_profile = get_api_profile(owner, request)
    AuditLog.objects.create(actor=request.user, target_user=owner, action='brand_enter', metadata={'brand_id': brand_id})
    return Response({
        'token': token.key,
        'user': _serialize_user(owner, owner_profile, request),
        'impersonated': True,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_plan_view(request, brand_id):
    caller = get_api_profile(request.user, request)
    if not is_api_superuser(request.user):
        return Response({
            'error': 'Plan değişikliği için ödeme akışını kullanın.',
            'code': 'use_checkout',
        }, status=status.HTTP_403_FORBIDDEN)
    try:
        brand = BusinessBrand.objects.get(id=brand_id)
    except BusinessBrand.DoesNotExist:
        return Response({'error': 'Marka bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    new_plan = request.data.get('plan')
    if new_plan not in PLAN_CHOICES:
        return Response({'error': 'Geçersiz plan seçimi.'}, status=status.HTTP_400_BAD_REQUEST)
    from restaurant.api.payment_service import create_pending_invoice, fulfill_subscription_payment, serialize_invoice
    invoice = create_pending_invoice(brand, new_plan)
    invoice.payment_provider = 'mock'
    invoice.save(update_fields=['payment_provider'])
    fulfill_subscription_payment(invoice)
    return Response({
        'message': 'Plan başarıyla güncellendi (yönetici ataması).',
        'brand': _serialize_brand(brand),
        'invoice': serialize_invoice(invoice),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plan_status_view(request):
    profile = get_api_profile(request.user, request)
    if is_api_superuser(request.user):
        return Response({'role': 'super_admin', 'unlimited': True, 'yonetim_url': '/yonetim/'})
    if not profile.brand:
        return Response({'error': 'Marka bulunamadı.'}, status=status.HTTP_400_BAD_REQUEST)
    brand = profile.brand
    plan = brand_plan(brand)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['starter'])
    owner = subscription_owner_for_brand(brand)
    trial_days = plan_trial_days(getattr(owner, 'active_plan', None) if owner else None)
    return Response({
        'brand_id': brand.id,
        'brand_name': brand.name,
        'plan': plan,
        'plan_display': limits['label'],
        'plan_status': get_plan_status(brand),
        'limits': limits,
        'usage': get_brand_usage(brand),
        'trial_days': trial_days,
        'all_plans': {
            key: {'label': val['label'], 'branches': val['branches'], 'staff': val['staff'], 'price': val['price']}
            for key, val in PLAN_LIMITS.items()
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_list_view(request):
    caller = get_api_profile(request.user, request)
    if is_api_superuser(request.user):
        invoices = Invoice.objects.all().order_by('-created_at')
    elif caller.brand:
        invoices = Invoice.objects.filter(brand=caller.brand).order_by('-created_at')
    else:
        invoices = Invoice.objects.none()
    from restaurant.api.payment_service import serialize_invoice
    result = []
    for inv in invoices:
        row = serialize_invoice(inv)
        row['brand_name'] = inv.brand.name
        result.append(row)
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def super_admin_stats_view(request):
    caller = get_api_profile(request.user, request)
    if not is_api_superuser(request.user):
        return Response({'error': 'Yetkisiz erişim.'}, status=status.HTTP_403_FORBIDDEN)
    hq_brands = BusinessBrand.objects.filter(panel_kind=BusinessBrand.PANEL_HQ)
    with_restaurant = hq_brands.filter(restaurant_tenant__isnull=False)
    return Response({
        'total_brands': with_restaurant.count(),
        'active_brands': with_restaurant.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'platform_metrics': {
            'total_branches': Branch.objects.count(),
            'active_franchise_panels': Branch.objects.filter(panel_enabled=True, is_active=True).count(),
        },
        'yonetim_url': '/yonetim/',
        'recent_brands': [_serialize_brand(b) for b in with_restaurant.order_by('-pk')[:5]],
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def seed_super_admin(request):
    if User.objects.exists():
        return Response({'error': 'Sistemde zaten kullanıcılar mevcut.'}, status=status.HTTP_400_BAD_REQUEST)
    if not settings.DEBUG:
        return Response({'error': 'Seed işlemi devre dışı.'}, status=status.HTTP_403_FORBIDDEN)
    username = request.data.get('username', 'admin')
    password = request.data.get('password', 'admin123')
    user = User.objects.create_superuser(username=username, password=password, email='admin@coolops.local')
    get_api_profile(user, request)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'message': 'Süper yönetici oluşturuldu.',
        'token': token.key,
        'user': _serialize_user(user, profile, request),
    }, status=status.HTTP_201_CREATED)
