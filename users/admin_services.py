"""Süper admin paneli — üyelik senkronizasyonu ve platform raporları."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()


def parse_membership_post(request):
    from core_settings.models import BrandMembership

    brand_roles: dict[int, str] = {}
    valid_roles = {choice[0] for choice in BrandMembership.ROLE_CHOICES}
    for raw in request.POST.getlist('brands'):
        if not str(raw).isdigit():
            continue
        brand_id = int(raw)
        role = request.POST.get(f'membership_role_{brand_id}', BrandMembership.ROLE_MEMBER)
        if role not in valid_roles:
            role = BrandMembership.ROLE_MEMBER
        brand_roles[brand_id] = role
    default_brand_id = None
    raw_default = request.POST.get('default_brand', '').strip()
    if raw_default.isdigit():
        default_brand_id = int(raw_default)
    return brand_roles, default_brand_id


def sync_user_brand_memberships(user, *, brand_roles: dict[int, str], default_brand_id: int | None):
    from common.brand_team import attach_user_to_brand
    from core_settings.models import BrandMembership, BusinessBrand

    existing_ids: set[int] = set()
    for brand_id, role in brand_roles.items():
        brand = BusinessBrand.objects.filter(pk=brand_id).first()
        if not brand:
            continue
        is_default = bool(default_brand_id and default_brand_id == brand_id)
        attach_user_to_brand(user, brand, membership_role=role, is_default=is_default)
        existing_ids.add(brand_id)

    if existing_ids and default_brand_id and default_brand_id in existing_ids:
        BrandMembership.objects.filter(user=user).exclude(brand_id=default_brand_id).update(
            is_default=False,
        )
        BrandMembership.objects.filter(user=user, brand_id=default_brand_id).update(is_default=True)
    elif existing_ids and not default_brand_id:
        first = BrandMembership.objects.filter(user=user, brand_id__in=existing_ids).first()
        if first and not BrandMembership.objects.filter(user=user, is_default=True).exists():
            BrandMembership.objects.filter(user=user).update(is_default=False)
            first.is_default = True
            first.save(update_fields=['is_default'])

    BrandMembership.objects.filter(user=user).exclude(brand_id__in=existing_ids).delete()


def admin_user_delete_context(actor, target):
    from core_settings.models import BrandMembership

    can_delete = True
    blocked_reason = ''
    if actor.pk == target.pk:
        can_delete = False
        blocked_reason = 'Kendi hesabınızı silemezsiniz.'
    elif target.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
        can_delete = False
        blocked_reason = 'Sistemdeki son süper admin silinemez.'

    memberships = list(
        BrandMembership.objects.filter(user=target).select_related('brand').order_by('brand__name')
    )
    owner_memberships = [m for m in memberships if m.role == BrandMembership.ROLE_OWNER]
    delete_warning = ''
    if can_delete and owner_memberships:
        names = ', '.join(m.brand.name for m in owner_memberships[:5])
        extra = len(owner_memberships) - 5
        if extra > 0:
            names += f' (+{extra})'
        delete_warning = (
            f'Bu kullanıcı şu markaların sahibi: {names}. '
            'Silme işlemi tüm marka üyeliklerini kaldırır; kullanıcı hesabı kalıcı silinir.'
        )
    elif can_delete and memberships:
        delete_warning = f'{len(memberships)} marka üyeliği kaldırılacak.'

    return {
        'user_can_delete': can_delete,
        'user_delete_blocked_reason': blocked_reason,
        'delete_memberships': memberships,
        'delete_warning': delete_warning,
    }


def platform_dashboard_stats():
    from common.brand_team import production_users_queryset, subscription_owners_queryset
    from core_settings.models import BusinessBrand, Plan

    owners = subscription_owners_queryset()
    brands = BusinessBrand.objects.all()
    active_brands = brands.filter(is_active=True)
    return {
        'total_users': owners.count(),
        'active_users': owners.filter(is_active=True).count(),
        'total_platform_users': production_users_queryset().exclude(is_superuser=True).count(),
        'total_brands': active_brands.count(),
        'inactive_brands': brands.filter(is_active=False).count(),
        'hq_brands': active_brands.filter(panel_kind=BusinessBrand.PANEL_HQ).count(),
        'dealer_brands': active_brands.filter(panel_kind=BusinessBrand.PANEL_DEALER).count(),
        'plans': list(
            Plan.objects.filter(is_active=True).annotate(
                owner_count=Count('users', distinct=True),
            ).order_by('price')
        ),
    }


def tenant_usage_rows():
    """Abonelik sahibi başına plan limit kullanımı."""
    from common.brand_team import subscription_owners_queryset
    from core_settings.models import BrandMembership, BusinessBrand
    from customers.models import Customer

    rows = []
    for owner in subscription_owners_queryset().prefetch_related('brand_memberships__brand'):
        plan = owner.active_plan
        owned_brands = [
            m.brand
            for m in owner.brand_memberships.all()
            if m.role == BrandMembership.ROLE_OWNER and m.brand.is_active
        ]
        hq_brands = [b for b in owned_brands if b.panel_kind == BusinessBrand.PANEL_HQ]
        dealer_brands = [b for b in owned_brands if b.panel_kind == BusinessBrand.PANEL_DEALER]
        brand_count = len(owned_brands)
        max_hq = getattr(plan, 'max_hq_brands', None) or plan.max_brands if plan else 0
        max_dealer = getattr(plan, 'max_dealer_panels', 0) if plan else 0
        max_users = plan.max_users_per_brand if plan else 0
        max_customers = plan.max_customers_per_brand if plan else 0
        max_brands = plan.max_brands if plan else 0

        brand_details = []
        for brand in owned_brands:
            user_count = BrandMembership.objects.filter(brand=brand).count()
            customer_count = Customer.objects.filter(brand=brand).count()
            brand_details.append({
                'brand': brand,
                'user_count': user_count,
                'customer_count': customer_count,
                'users_pct': _pct(user_count, max_users),
                'customers_pct': _pct(customer_count, max_customers),
                'users_warn': max_users and user_count >= max_users * 0.9,
                'customers_warn': max_customers and customer_count >= max_customers * 0.9,
            })

        rows.append({
            'owner': owner,
            'plan': plan,
            'brand_count': brand_count,
            'hq_count': len(hq_brands),
            'dealer_count': len(dealer_brands),
            'hq_limit': max_hq,
            'dealer_limit': max_dealer,
            'brands_limit': max_brands,
            'brands_pct': _pct(brand_count, max_brands),
            'brands_warn': max_brands and brand_count >= max_brands * 0.9,
            'hq_warn': max_hq and len(hq_brands) >= max_hq * 0.9,
            'dealer_warn': max_dealer and len(dealer_brands) >= max_dealer * 0.9,
            'brand_details': brand_details,
        })
    return rows


def platform_relations_context():
    from common.brand_team import subscription_owners_queryset
    from core_settings.models import BrandMembership, BusinessBrand, Plan

    hierarchy, orphan_dealers = brand_hierarchy_rows()
    usage_rows = tenant_usage_rows()
    owners = list(subscription_owners_queryset().select_related('plan').prefetch_related('brand_memberships__brand'))
    subscription_rows = []
    for owner in owners:
        owned = [m for m in owner.brand_memberships.all() if m.role == BrandMembership.ROLE_OWNER]
        hq = [m.brand for m in owned if m.brand.panel_kind == BusinessBrand.PANEL_HQ and m.brand.is_active]
        dealers = [m.brand for m in owned if m.brand.panel_kind == BusinessBrand.PANEL_DEALER and m.brand.is_active]
        subscription_rows.append({
            'owner': owner,
            'plan': owner.active_plan,
            'hq_brands': hq,
            'dealer_panels': dealers,
        })

    issues = []
    for dealer in orphan_dealers:
        issues.append({'kind': 'orphan_dealer', 'label': dealer.name, 'url_name': 'admin_brand_edit', 'pk': dealer.pk})
    for row in usage_rows:
        if not row['owner'].plan_id:
            issues.append({'kind': 'no_plan', 'label': row['owner'].display_name, 'url_name': 'admin_user_edit', 'pk': row['owner'].pk})
        if row.get('brands_warn') or row.get('hq_warn') or row.get('dealer_warn'):
            issues.append({'kind': 'limit', 'label': row['owner'].display_name, 'url_name': 'admin_user_edit', 'pk': row['owner'].pk})
    super_with_brands = BrandMembership.objects.filter(user__is_superuser=True).count()
    if super_with_brands:
        issues.append({'kind': 'super_owner', 'label': f'{super_with_brands} süper admin üyeliği', 'url_name': 'admin_users', 'pk': None})

    return {
        'hierarchy': hierarchy,
        'orphan_dealers': orphan_dealers,
        'membership_matrix': membership_matrix_rows(),
        'subscription_rows': subscription_rows,
        'usage_rows': usage_rows,
        'issues': issues,
        'plan_distribution': list(
            Plan.objects.filter(is_active=True).annotate(
                owner_count=Count('users', distinct=True),
            ).order_by('price')
        ),
        'stats': {
            'owner_count': len(owners),
            'hq_count': BusinessBrand.objects.filter(is_active=True, panel_kind=BusinessBrand.PANEL_HQ).count(),
            'dealer_count': BusinessBrand.objects.filter(is_active=True, panel_kind=BusinessBrand.PANEL_DEALER).count(),
            'inactive_brands': BusinessBrand.objects.filter(is_active=False).count(),
        },
    }


def platform_summary_stats():
    from core_settings.models import BrandMembership, BusinessBrand
    from customers.models import Customer
    from services.models import ServiceRecord

    active_brand_ids = BusinessBrand.objects.filter(is_active=True).values_list('pk', flat=True)
    return {
        'total_customers': Customer.objects.filter(brand_id__in=active_brand_ids).count(),
        'total_services': ServiceRecord.objects.filter(brand_id__in=active_brand_ids).count(),
        'total_memberships': BrandMembership.objects.filter(brand_id__in=active_brand_ids).count(),
        'brands_with_data': BusinessBrand.objects.filter(
            is_active=True,
        ).annotate(
            customer_count=Count('customers', distinct=True),
        ).filter(customer_count__gt=0).count(),
    }


def brand_hierarchy_rows():
    from core_settings.models import BusinessBrand

    hq_brands = (
        BusinessBrand.objects.filter(is_active=True, panel_kind=BusinessBrand.PANEL_HQ)
        .prefetch_related('dealer_panels')
        .order_by('name')
    )
    rows = []
    for hq in hq_brands:
        dealers = [d for d in hq.dealer_panels.all() if d.is_active]
        rows.append({'hq': hq, 'dealers': dealers})
    orphan_dealers = BusinessBrand.objects.filter(
        is_active=True,
        panel_kind=BusinessBrand.PANEL_DEALER,
        parent_brand__isnull=True,
    )
    return rows, list(orphan_dealers)


def _pct(value: int, limit: int) -> int:
    if not limit:
        return 0
    return min(100, int(round(value * 100 / limit)))


def brand_delete_stats(brand):
    from core_settings.models import FinanceRecord, ServicePersonnel, SolutionPartner
    from customers.models import Customer
    from services.models import ServiceRecord

    return {
        'customers': Customer.objects.filter(brand=brand).count(),
        'services': ServiceRecord.objects.filter(brand=brand).count(),
        'memberships': brand.memberships.count(),
        'dealers': brand.dealer_panels.count(),
        'personnel': ServicePersonnel.objects.filter(brand=brand).count(),
        'finance_records': FinanceRecord.objects.filter(brand=brand).count(),
        'solution_partners': SolutionPartner.objects.filter(brand=brand).count(),
    }


def brand_delete_context(brand):
    stats = brand_delete_stats(brand)
    can_delete = True
    blocked_reason = ''
    if brand.is_default:
        can_delete = False
        blocked_reason = 'Sistem varsayılan markası silinemez.'
    has_tenant_data = any(
        stats[key] for key in ('customers', 'services', 'personnel', 'finance_records', 'solution_partners')
    )
    return {
        'brand_can_delete': can_delete,
        'brand_delete_blocked_reason': blocked_reason,
        'brand_delete_stats': stats,
        'brand_requires_wipe': has_tenant_data or stats['dealers'] > 0,
        'brand_delete_warning': _brand_delete_warning(brand, stats, has_tenant_data),
    }


def _brand_delete_warning(brand, stats, has_tenant_data):
    parts = []
    if stats['dealers']:
        parts.append(f'{stats["dealers"]} bayi paneli')
    if stats['customers']:
        parts.append(f'{stats["customers"]} müşteri')
    if stats['services']:
        parts.append(f'{stats["services"]} servis kaydı')
    if stats['memberships']:
        parts.append(f'{stats["memberships"]} kullanıcı üyeliği')
    if not parts:
        return 'Marka kalıcı olarak silinecek.'
    return f'Kalıcı silme: {", ".join(parts)} kaldırılır.'


def _wipe_brand_tenant_data(brand):
    from core_settings.models import FinanceRecord, ServicePersonnel, SolutionPartner
    from customers.models import Customer
    from services.models import ServiceRecord

    ServiceRecord.objects.filter(brand=brand).delete()
    Customer.objects.filter(brand=brand).delete()
    ServicePersonnel.objects.filter(brand=brand).delete()
    SolutionPartner.objects.filter(brand=brand).delete()
    FinanceRecord.objects.filter(brand=brand).delete()


def purge_and_delete_brand(brand):
    from core_settings.models import BusinessBrand
    from django.db import transaction

    with transaction.atomic():
        for dealer in BusinessBrand.objects.filter(parent_brand=brand):
            purge_and_delete_brand(dealer)
        _wipe_brand_tenant_data(brand)
        name = brand.name
        brand.delete()
        return name


def user_delete_context_basic(actor, target):
    ctx = admin_user_delete_context(actor, target)
    return {
        'user_can_delete': ctx['user_can_delete'],
        'user_delete_blocked_reason': ctx['user_delete_blocked_reason'],
    }


def reassign_brand_owner(brand, new_owner):
    from common.brand_team import attach_user_to_brand
    from common.plan_sync import sync_brand_plan_from_owner
    from core_settings.models import BrandMembership
    from django.db import transaction
    from users.utils import get_or_create_user_profile

    if new_owner.is_superuser:
        raise ValueError('Süper admin marka sahibi olamaz.')

    with transaction.atomic():
        previous_owners = list(
            BrandMembership.objects.filter(
                brand=brand,
                role=BrandMembership.ROLE_OWNER,
            ).exclude(user=new_owner).select_related('user')
        )
        BrandMembership.objects.filter(
            brand=brand,
            role=BrandMembership.ROLE_OWNER,
        ).exclude(user=new_owner).update(role=BrandMembership.ROLE_MEMBER)
        attach_user_to_brand(
            new_owner,
            brand,
            membership_role=BrandMembership.ROLE_OWNER,
            is_default=False,
        )
        if new_owner.plan_id is None and brand.panel_kind == brand.PANEL_HQ:
            from common.brand_team import subscription_owner_for_brand
            existing = subscription_owner_for_brand(brand)
            if existing and existing.plan_id:
                new_owner.plan_id = existing.plan_id
                new_owner.save(update_fields=['plan_id'])

        for mem in previous_owners:
            profile = get_or_create_user_profile(mem.user)
            if profile.restaurant_brand_id == brand.pk:
                profile.restaurant_brand = None
                if profile.restaurant_role == 'store_owner':
                    profile.restaurant_role = ''
                profile.save(update_fields=['restaurant_brand', 'restaurant_role'])

        from restaurant.onboarding import apply_restaurant_owner_setup

        apply_restaurant_owner_setup(new_owner, brand)
        sync_brand_plan_from_owner(new_owner, brand)


def strip_superuser_brand_memberships(user=None) -> int:
    """Süper admin kullanıcıların marka üyeliklerini kaldırır."""
    from core_settings.models import BrandMembership

    qs = User.objects.filter(is_superuser=True)
    if user is not None:
        if not user.is_superuser:
            return 0
        qs = qs.filter(pk=user.pk)
    ids = list(qs.values_list('pk', flat=True))
    if not ids:
        return 0
    deleted, _ = BrandMembership.objects.filter(user_id__in=ids).delete()
    return deleted


def membership_matrix_rows():
    from core_settings.models import BrandMembership

    rows = []
    for mem in (
        BrandMembership.objects.select_related('user', 'brand', 'user__role')
        .filter(brand__is_active=True, user__is_superuser=False)
        .order_by('brand__name', 'user__username')
    ):
        rows.append({
            'membership': mem,
            'user': mem.user,
            'brand': mem.brand,
        })
    return rows


def can_change_superuser_status(editor, target, *, promote: bool) -> tuple[bool, str]:
    if not editor or not editor.is_superuser:
        return False, 'Yetkiniz yok.'
    live_superusers = User.objects.filter(is_superuser=True).exclude(
        username__startswith='_rbac_',
    )
    if target.pk == editor.pk and not promote:
        if live_superusers.count() <= 1:
            return False, 'Son süper admin yetkisini kaldıramazsınız.'
    if not promote and target.is_superuser and live_superusers.count() <= 1:
        return False, 'Sistemdeki son süper admin pasifleştirilemez.'
    return True, ''


def usage_report_csv_rows():
    rows = [['Abonelik sahibi', 'Plan', 'Marka', 'Kullanıcı', 'Müşteri', 'Kullanıcı limit %', 'Müşteri limit %']]
    for row in tenant_usage_rows():
        owner = row['owner']
        plan = row['plan']
        for detail in row['brand_details']:
            rows.append([
                owner.display_name,
                plan.name if plan else '',
                detail['brand'].name,
                detail['user_count'],
                detail['customer_count'],
                detail['users_pct'],
                detail['customers_pct'],
            ])
    return rows
