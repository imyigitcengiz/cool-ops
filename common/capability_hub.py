"""Entegrasyon merkezi — KPI ve durum özeti."""

from __future__ import annotations

from common.module_catalog import MODULE_KIND_INTEGRATION, MODULES
from common.module_runtime import build_module_record, is_module_enabled, module_available_for_nav


def _whatsapp_connection_count() -> int:
    try:
        from tools.models import WhatsappConnection
        return WhatsappConnection.objects.exclude(last_connected_at__isnull=True).count()
    except Exception:
        return 0


def _scraped_firm_count() -> int:
    try:
        from tools.models import MapsScrapedFirm
        return MapsScrapedFirm.objects.count()
    except Exception:
        return 0


def integration_status_hint(slug: str) -> str:
    if slug == 'integration_whatsapp_bridge':
        n = _whatsapp_connection_count()
        return f'{n} aktif hat' if n else 'Hat bağlanmadı'
    if slug == 'integration_data_harvest':
        n = _scraped_firm_count()
        return f'{n} kayıtlı firma'
    if slug == 'integration_media':
        return 'Medya arşivi'
    if slug == 'integration_whatsapp_api':
        try:
            from core_settings.models import SiteSettings
            s = SiteSettings.objects.first()
            if s and getattr(s, 'whatsapp_cloud_access_token', ''):
                return 'API yapılandırıldı'
        except Exception:
            pass
        return 'Token girilmedi'
    return 'Hazır'


def build_capabilities_hub_context(user) -> dict:
    items = []
    for mod in MODULES:
        if mod['kind'] != MODULE_KIND_INTEGRATION:
            continue
        rec = build_module_record(user, mod)
        rec['status_hint'] = integration_status_hint(mod['slug'])
        rec['available'] = module_available_for_nav(user, mod['slug'])
        items.append(rec)

    items.sort(key=lambda x: (x.get('sort', 99), x['name']))
    enabled = sum(1 for c in items if is_module_enabled(c['slug']))
    return {
        'capability_groups': [{
            'slug': 'entegrasyon',
            'name': 'Entegrasyonlar',
            'icon': 'zap',
            'items': items,
        }] if items else [],
        'capabilities_flat': items,
        'capabilities_total': len(items),
        'capabilities_enabled': enabled,
    }
