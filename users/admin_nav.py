"""Süper admin sidebar — config-driven navigasyon grupları."""

from __future__ import annotations

def _nav_item(url_name, label, icon, active_url_names=()):
    return {
        'url_name': url_name,
        'label': label,
        'icon': icon,
        'active_url_names': tuple(active_url_names) or (url_name,),
    }


def admin_nav_groups(current_url_name: str | None = None, request=None) -> list[dict]:
    """Sidebar grupları; her öğede `active` bayrağı."""
    from common.panel_env import panel_git_updates_enabled

    git_updates = panel_git_updates_enabled()

    groups: list[dict] = [
        {
            'key': 'top',
            'label': '',
            'items': [
                _nav_item('admin_dashboard', 'Özet', 'layout-dashboard'),
            ],
        },
        {
            'key': 'platform',
            'label': 'Platform',
            'items': [
                _nav_item(
                    'admin_users', 'Kullanıcılar', 'users',
                    ('admin_users', 'admin_user_create', 'admin_user_edit', 'admin_user_delete'),
                ),
                _nav_item(
                    'admin_brands', 'Markalar', 'store',
                    (
                        'admin_brands', 'admin_brand_create', 'admin_brand_detail',
                        'admin_brand_edit', 'admin_brand_deactivate', 'admin_brand_activate',
                        'admin_brand_delete', 'admin_brand_inspect',
                    ),
                ),
                _nav_item('admin_relations', 'Platform ilişkileri', 'git-branch'),
            ],
        },
        {
            'key': 'app_selection',
            'label': 'Uygulama Seçimi',
            'items': [
                _nav_item('admin_applications', 'Uygulama Modülleri', 'layout-grid'),
                _nav_item('admin_panels', 'Paneller', 'monitor'),
            ],
        },
        {
            'key': 'subscription',
            'label': 'Abonelik',
            'items': [
                _nav_item(
                    'admin_plans', 'Planlar', 'credit-card',
                    ('admin_plans', 'admin_plan_create', 'admin_plan_edit'),
                ),
                _nav_item(
                    'admin_invoices', 'Faturalar', 'receipt',
                    ('admin_invoices', 'admin_invoice_create'),
                ),
            ],
        },
        {
            'key': 'management',
            'label': 'Yönetim',
            'items': [
                _nav_item(
                    'admin_roles', 'Sistem rolleri', 'shield-check',
                    ('admin_roles', 'admin_role_create', 'admin_role_edit', 'admin_role_delete'),
                ),
                _nav_item(
                    'admin_reports', 'Raporlar', 'bar-chart-3',
                    ('admin_reports', 'admin_reports_usage'),
                ),
            ],
        },
        {
            'key': 'system',
            'label': 'Sistem',
            'items': [
                _nav_item('admin_site_settings', 'Site ayarları', 'settings'),
                _nav_item('admin_audit_log', 'Denetim', 'scroll-text'),
                _nav_item('admin_system_backup', 'Yedek & sıfırlama', 'database-backup'),
            ],
        },
    ]

    if git_updates:
        groups[-1]['items'].append(
            _nav_item('admin_system_updates', 'Uygulama güncellemeleri', 'refresh-cw')
        )

    footer_items = [
        _nav_item('admin_panels', 'Marka panelleri', 'scan-eye'),
        _nav_item('profile_settings', 'Profilim', 'user'),
    ]

    for group in groups:
        for item in group['items']:
            item['active'] = current_url_name in item['active_url_names']

    for item in footer_items:
        item['active'] = current_url_name in item['active_url_names']

    return groups + [{'key': 'footer', 'label': '', 'items': footer_items, 'border_top': True}]
