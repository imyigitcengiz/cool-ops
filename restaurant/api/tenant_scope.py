"""Şube (branch) bazlı veri izolasyonu yardımcıları."""

from restaurant.compat import get_api_profile
from restaurant.api.security import is_api_superuser
from restaurant.models import Branch, FranchisePanelToken


def get_franchise_branch(request):
    token_key = request.headers.get('Franchise-Token') or request.headers.get('X-Franchise-Token')
    if not token_key:
        return None
    try:
        token = FranchisePanelToken.objects.select_related('branch', 'branch__brand').get(key=token_key)
        branch = token.branch
        if branch.panel_enabled and branch.is_active:
            return branch
    except FranchisePanelToken.DoesNotExist:
        pass
    return None


def get_branch_id_from_request(request):
    branch = get_franchise_branch(request)
    if branch:
        return branch.id
    raw = request.query_params.get('branch_id')
    if raw:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
    return None


def resolve_branch_for_user(request, branch_id):
    if not branch_id or not request.user.is_authenticated:
        return None
    profile = get_api_profile(request.user, request)
    brand = profile.brand
    if not brand:
        return None
    if is_api_superuser(request.user):
        return Branch.objects.filter(id=branch_id).first()
    return Branch.objects.filter(id=branch_id, brand_id=brand.pk).first()


def filter_by_tenant(queryset, request, brand_field='brand', branch_field='branch'):
    user = request.user
    if not user.is_authenticated:
        return queryset.none()

    profile = get_api_profile(user, request)
    if not is_api_superuser(user):
        brand = profile.brand
        if brand:
            queryset = queryset.filter(**{brand_field: brand})
        else:
            return queryset.model.objects.none()

    branch_id = get_branch_id_from_request(request)
    if branch_id and not get_franchise_branch(request):
        branch = resolve_branch_for_user(request, branch_id)
        if branch:
            queryset = queryset.filter(**{branch_field: branch_id})
        elif not is_api_superuser(user):
            return queryset.model.objects.none()

    return queryset


def branch_order_filter(branch):
    from django.db.models import Q
    return Q(branch=branch) | Q(branch__isnull=True, table__branch=branch)
