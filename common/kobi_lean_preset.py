"""KOBİ montaj/servis için sade varsayılan modül profili.

Yeni kurulumlar ve `apply_lean_kobi_preset` komutu bu listeyi kullanır.
İsteğe bağlı modüller Modül Merkezi'nden açılabilir.
"""

from __future__ import annotations

# Çekirdek uygulama modülleri
LEAN_KOBI_MODULES: tuple[str, ...] = (
    'contact',
    'services',
    'accounting',
    'settings',
    'integration_whatsapp_bridge',
)

# Temel parçacıklar (personel, maaş, gelir-gider, satış, kasa)
LEAN_KOBI_PARTICLES: tuple[str, ...] = (
    'p.contact.customers',
    'p.contact.firms',
    'p.contact.teams',
    'p.accounting.personnel',
    'p.accounting.payroll',
    'p.accounting.finance',
    'p.accounting.sales',
    'p.accounting.cash',
)

# Eski “her şey açık” KOBİ paketi — migration / komut karşılaştırması
LEGACY_BLOATED_MODULES: frozenset[str] = frozenset({
    'contact', 'services', 'accounting', 'outreach', 'settings',
    'supplier_payables', 'e_invoice_bridge', 'project_costing', 'multi_cash',
    'projects', 'timesheet',
    'integration_data_harvest', 'integration_whatsapp_bridge',
    'integration_whatsapp_api', 'integration_media', 'integration_weather',
})

LEGACY_BLOATED_PARTICLES: frozenset[str] = frozenset({
    'p.contact.customers', 'p.contact.firms', 'p.contact.teams',
    'p.accounting.personnel', 'p.accounting.payroll',
    'p.accounting.finance', 'p.accounting.sales',
    'p.accounting.cash', 'p.accounting.receivables', 'p.accounting.stock',
    'p.accounting.payables', 'p.accounting.multi_cash', 'p.accounting.project_costing',
    'p.accounting.e_export', 'p.accounting.timesheet', 'p.accounting.projects',
    'p.outreach.campaigns',
})


def lean_kobi_slugs() -> list[str]:
    return list(LEAN_KOBI_MODULES) + list(LEAN_KOBI_PARTICLES)


def full_finance_extension_slugs() -> list[str]:
    """Testler ve genişletilmiş kurulumlar — tüm finans uzantıları açık."""
    return lean_kobi_slugs() + [
        'supplier_payables', 'e_invoice_bridge', 'project_costing', 'multi_cash',
        'projects', 'timesheet', 'integration_weather',
        'p.accounting.receivables', 'p.accounting.stock',
        'p.accounting.payables', 'p.accounting.multi_cash', 'p.accounting.project_costing',
        'p.accounting.e_export', 'p.accounting.timesheet', 'p.accounting.projects',
    ]


def is_legacy_bloated_preset(stored: list | tuple | None) -> bool:
    """Kayıtlı liste eski tam KOBİ paketine eşit veya onu içeriyorsa."""
    if not stored:
        return False
    current = set(stored)
    legacy = LEGACY_BLOATED_MODULES | LEGACY_BLOATED_PARTICLES
    return legacy.issubset(current) and current.issubset(legacy | {'settings'})
