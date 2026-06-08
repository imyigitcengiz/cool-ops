"""Ortak şablon bağlamı."""

from common import module_labels as ml
from common.capability_routing import resolve_capabilities_hub_url
from common.module_runtime import (
    build_module_sidebar,
    build_modules_nav_flags,
    build_particles_nav_short,
    get_enabled_module_slugs,
)


def gy_branding(request):
    """Modül adları — şablonlarda {{ gy.rehber }}, {{ gy.yardim_masasi }} vb."""
    return {
        'gy': {
            'app_name': ml.APP_NAME,
            'kobiops': ml.PRODUCT_KOBIOPS,
            'kobipos': ml.PRODUCT_KOBIPOS,
            'app_tagline': ml.APP_TAGLINE,
            'ana_panel': ml.ANA_PANEL,
            'ozellikler': ml.OZELLIKLER,
            'modul_merkezi': ml.MODUL_MERKEZI,
            'entegrasyon_merkezi': ml.ENTEGRASYON_MERKEZI,
            'araclar': ml.ARACLAR,
            'medya_kutuphanesi': ml.MEDYA_KUTUPHANESI,
            'site_ayarlari': ml.SITE_AYARLARI,
            'iletisim_merkezi': ml.ILETISIM_MERKEZI,
            'rehber': ml.REHBER,
            'yardim_masasi': ml.YARDIM_MASASI,
            'satis_birimi': ml.SATIS_BIRIMI,
            'muhasebe': ml.MUHASEBE,
            'ym_ozet': ml.YM_OZET,
            'ym_kayitlar': ml.YM_KAYITLAR,
            'ym_saha_plani': ml.YM_SAHA_PLANI,
            'ym_durumlar': ml.YM_DURUMLAR,
            'ym_ariza': ml.YM_ARIZA_TIPLERI,
            'ym_oncelikler': ml.YM_ONCELIKLER,
            'rehber_ozet': ml.REHBER_OZET,
            'rehber_musteriler': ml.REHBER_MUSTERILER,
            'rehber_firmalar': ml.REHBER_FIRMALAR,
            'rehber_firma_bul': ml.REHBER_FIRMA_BUL,
            'rehber_ekipler': ml.REHBER_EKIPLER,
            'rehber_personel': ml.REHBER_PERSONEL,
            'rehber_musteri_360': ml.REHBER_MUSTERI_360,
            'sb_ozet': ml.SB_OZET,
            'sb_kayitlar': ml.SB_KAYITLAR,
            'sb_teklifler': ml.SB_TEKLIFLER,
            'mh_ozet': ml.MH_OZET,
            'mh_maas_avans': ml.MH_MAAS_AVANS,
            'mh_personel': ml.MH_PERSONEL,
            'mh_raporlar': ml.MH_RAPORLAR,
            'mh_gelir_gider': ml.MH_GELIR_GIDER,
            'mh_kasa': ml.MH_KASA,
            'mh_stok': ml.MH_STOK,
            'mh_alacaklar': ml.MH_ALACAKLAR,
            'mh_veri_alisverisi': ml.MH_VERI_ALISVERISI,
            'mh_borclar': ml.MH_BORCLAR,
            'mh_hesaplar': ml.MH_HESAPLAR,
            'mh_proje_karlilik': ml.MH_PROJE_KARLILIK,
            'mh_dis_aktarim': ml.MH_DIS_AKTARIM,
            'mh_zaman': ml.MH_ZAMAN,
            'mh_projeler': ml.MH_PROJELER,
            'mh_maas_raporu': ml.MH_MAAS_RAPORU,
            'mh_tagline': ml.MH_TAGLINE,
            'sb_rapor': ml.SB_RAPOR,
            'ortak_urunler': ml.ORTAK_URUNLER,
        },
    }


def module_install_context(request):
    from common.erp_shell import build_erp_shell_context

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        shell = build_erp_shell_context(request)
        return {
            'modules_installed': {},
            'modules_nav': {},
            'particles_nav': {},
            'module_sidebar': {'groups': [], 'capabilities': [], 'integrations': [], 'integrations_by_section': {}},
            'profile_sidebar': {'groups': [], 'capabilities': [], 'integrations': [], 'integrations_by_section': {}},
            'capabilities_hub_url': None,
            'can_manage_modules': False,
            'panel_integrations': [],
            **shell,
        }
    from common.request_cache import cache_get
    from common.module_runtime import build_panel_integrations

    enabled_slugs = cache_get(request, 'enabled_module_slugs', get_enabled_module_slugs)
    installed = {slug: slug in enabled_slugs for slug in _all_module_slugs()}
    sidebar = cache_get(
        request,
        'module_sidebar',
        lambda: build_module_sidebar(user, request),
    )
    can_manage_modules = user.is_superuser or user.has_perm_codename('access.settings')
    panel_integrations = cache_get(
        request,
        'panel_integrations',
        lambda: build_panel_integrations(user),
    )
    return {
        'modules_installed': installed,
        'modules_nav': cache_get(request, 'modules_nav', lambda: build_modules_nav_flags(user)),
        'particles_nav': cache_get(request, 'particles_nav', lambda: build_particles_nav_short(user)),
        'module_sidebar': sidebar,
        'profile_sidebar': sidebar,
        'capabilities_hub_url': resolve_capabilities_hub_url(),
        'can_manage_modules': can_manage_modules,
        'panel_integrations': panel_integrations,
        **build_erp_shell_context(request),
    }


def tenant_context(request):
    from common.brand_access import (
        resolve_post_login_url,
        user_can_access_platform_panel,
        user_is_dealer_only,
    )
    from common.brand_team import can_manage_brand_team
    from common.tenant import build_brand_public_url

    tenant = getattr(request, 'tenant_brand', None)
    user = getattr(request, 'user', None)
    is_dealer_only = user_is_dealer_only(user) if user and user.is_authenticated else False
    return {
        'tenant_brand': tenant,
        'tenant_path_prefix': getattr(request, 'tenant_path_prefix', '') or '',
        'is_dealer_panel': bool(tenant and tenant.panel_kind == 'dealer'),
        'is_tenant_host': bool(tenant),
        'user_is_dealer_only': is_dealer_only,
        'user_can_access_platform': user_can_access_platform_panel(user) if user and user.is_authenticated else False,
        'user_can_manage_brand_team': can_manage_brand_team(user) if user and user.is_authenticated else False,
        'tenant_panel_url': build_brand_public_url(tenant, request) if tenant else '',
        'dealer_home_url': resolve_post_login_url(request, user) if is_dealer_only else '',
    }


def active_brand_context(request):
    from common.brand_scope import get_active_brand, user_brands, user_memberships

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'active_brand': None,
            'user_brands': [],
            'user_brand_memberships': [],
            'has_multiple_brands': False,
        }
    brands = list(user_brands(user))
    active = get_active_brand(request)
    return {
        'active_brand': active,
        'user_brands': brands,
        'user_brand_memberships': list(user_memberships(user)),
        'has_multiple_brands': len(brands) > 1,
    }


def _all_module_slugs():
    from common.module_catalog import MODULES
    return [m['slug'] for m in MODULES]


def admin_nav_context(request):
    """Süper admin sidebar — yalnızca /yonetim/ altında."""
    if not getattr(request, 'path', '').startswith('/yonetim/'):
        return {}
    match = getattr(request, 'resolver_match', None)
    url_name = getattr(match, 'url_name', None) if match else None
    from users.admin_nav import admin_nav_groups

    return {'admin_nav_groups': admin_nav_groups(url_name, request)}
