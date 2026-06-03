"""Aktif marka / firma kapsamı — oturum, üyelik ve queryset filtreleri."""

from __future__ import annotations

from django.db.models import Q, QuerySet

SESSION_ACTIVE_BRAND = 'active_brand_id'


def user_brands(user):
    from core_settings.models import BusinessBrand

    if not user or not getattr(user, 'is_authenticated', False) or not user.is_authenticated:
        return BusinessBrand.objects.none()
    qs = BusinessBrand.objects.filter(is_active=True)
    if user.is_superuser:
        return qs.order_by('name')
    return qs.filter(memberships__user=user).distinct().order_by('name')


def user_memberships(user):
    from core_settings.models import BrandMembership

    if not user or not user.is_authenticated:
        return BrandMembership.objects.none()
    return (
        BrandMembership.objects.filter(user=user, brand__is_active=True)
        .select_related('brand')
        .order_by('brand__name')
    )


def default_brand_for_user(user):
    from core_settings.models import BrandMembership

    if not user or not user.is_authenticated:
        return None
    mem = (
        BrandMembership.objects.filter(user=user, brand__is_active=True, is_default=True)
        .select_related('brand')
        .first()
    )
    if mem:
        return mem.brand
    mem = (
        BrandMembership.objects.filter(user=user, brand__is_active=True)
        .select_related('brand')
        .order_by('joined_at')
        .first()
    )
    return mem.brand if mem else None


def system_default_brand():
    from core_settings.models import BusinessBrand

    return (
        BusinessBrand.objects.filter(is_default=True, is_active=True).first()
        or BusinessBrand.objects.filter(is_active=True).order_by('pk').first()
    )


def _brand_id_allowed_for_user(user, brand_id: int) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        from core_settings.models import BusinessBrand

        return BusinessBrand.objects.filter(pk=brand_id, is_active=True).exists()
    from core_settings.models import BrandMembership

    return BrandMembership.objects.filter(user=user, brand_id=brand_id, brand__is_active=True).exists()


def get_active_brand_id(request) -> int | None:
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return None
    cached = getattr(request, '_active_brand_id', None)
    if cached is not None:
        return cached or None
    raw = request.session.get(SESSION_ACTIVE_BRAND)
    if raw:
        try:
            bid = int(raw)
        except (TypeError, ValueError):
            bid = None
        else:
            if bid and _brand_id_allowed_for_user(request.user, bid):
                request._active_brand_id = bid
                return bid
    default = default_brand_for_user(request.user) or system_default_brand()
    bid = default.pk if default else None
    request._active_brand_id = bid
    return bid


def get_active_brand(request):
    from core_settings.models import BusinessBrand

    bid = get_active_brand_id(request)
    if not bid:
        return None
    cached = getattr(request, '_active_brand_obj', None)
    if cached is not None and cached.pk == bid:
        return cached
    brand = BusinessBrand.objects.filter(pk=bid, is_active=True).first()
    request._active_brand_obj = brand
    return brand


def set_active_brand(request, brand_id: int) -> bool:
    if not _brand_id_allowed_for_user(request.user, brand_id):
        return False
    request.session[SESSION_ACTIVE_BRAND] = brand_id
    request._active_brand_id = brand_id
    request._active_brand_obj = None
    return True


def ensure_session_brand(request) -> None:
    """Middleware: oturumda geçerli aktif marka yoksa varsayılanı yaz."""
    if not request.user.is_authenticated:
        return
    bid = get_active_brand_id(request)
    if bid:
        request.session[SESSION_ACTIVE_BRAND] = bid


def filter_by_brand(qs: QuerySet, request, *, field: str = 'brand') -> QuerySet:
    bid = get_active_brand_id(request)
    if not bid or not hasattr(qs.model, field):
        return qs
    return qs.filter(**{f'{field}_id': bid})


def filter_customers(qs: QuerySet, request) -> QuerySet:
    return filter_by_brand(qs, request, field='brand')


def filter_services(qs: QuerySet, request) -> QuerySet:
    bid = get_active_brand_id(request)
    if not bid:
        return qs
    return qs.filter(Q(brand_id=bid) | Q(customer__brand_id=bid)).distinct()


def filter_finance(qs: QuerySet, request) -> QuerySet:
    return filter_by_brand(qs, request, field='brand')


def assign_brand(instance, request, *, field: str = 'brand') -> None:
    if getattr(instance, f'{field}_id', None):
        return
    bid = get_active_brand_id(request)
    if bid:
        setattr(instance, f'{field}_id', bid)


def create_brand_for_user(user, name: str, **extra):
    """Yeni marka oluşturur; kullanıcıyı sahip yapar."""
    from core_settings.models import BrandMembership, BusinessBrand

    name = (name or '').strip()
    if not name:
        raise ValueError('Marka adı gerekli.')
    has_any = BrandMembership.objects.filter(user=user).exists()
    brand = BusinessBrand.objects.create(
        name=name,
        created_by=user,
        is_default=not BusinessBrand.objects.exists(),
        **{k: v for k, v in extra.items() if k in ('legal_name', 'phone', 'address', 'currency_code')},
    )
    BrandMembership.objects.create(
        user=user,
        brand=brand,
        role=BrandMembership.ROLE_OWNER,
        is_default=not has_any,
    )
    return brand
