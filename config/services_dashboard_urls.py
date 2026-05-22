from django.urls import path, include
from django.views.generic import RedirectView

from analytics.views import DashboardView
from services.views import (
    ServiceListView, ServiceCreateView, ServiceUpdateView, ServiceDeleteView,
    ServicePrintView, ServiceBulkPrintView, bulk_delete_services, send_services_whatsapp, send_services_whatsapp_auto,
    quick_update_service_field, service_quick_edit_api, bulk_manage_services, restore_service_history_entry,
    service_status_change_preview_api,
    service_status_change_apply_api,
    service_whatsapp_status_confirm_api,
    customer_service_summary_api,
    service_reopen_api,
)
from core_settings.views import (
    SiteSettingsView,
    settings_api,
    options_catalog_api,
    service_types_for_products_api,
    quick_option_create_api,
    quick_option_update_api,
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),

    # Services
    path('services/', ServiceListView.as_view(), name='services'),
    path('services/new/', ServiceCreateView.as_view(), name='service_create'),
    path('services/musteri/<int:customer_id>/ozet/', customer_service_summary_api, name='customer_service_summary_api'),
    path('services/<int:pk>/yeniden-ac/', service_reopen_api, name='service_reopen'),
    path('services/<int:pk>/edit/', ServiceUpdateView.as_view(), name='service_update'),
    path('services/<int:pk>/delete/', ServiceDeleteView.as_view(), name='service_delete'),
    path('services/<int:pk>/print/', ServicePrintView.as_view(), name='service_print'),
    path('services/<int:pk>/quick-edit/', service_quick_edit_api, name='service_quick_edit_api'),
    path('services/<int:pk>/history/<int:history_id>/restore/', restore_service_history_entry, name='service_restore_history'),
    path('services/bulk-print/', ServiceBulkPrintView.as_view(), name='service_bulk_print'),
    path('services/bulk-delete/', bulk_delete_services, name='service_bulk_delete'),
    path('services/bulk-manage/', bulk_manage_services, name='service_bulk_manage'),
    path('services/quick-update/', quick_update_service_field, name='service_quick_update'),
    path('services/whatsapp/durum-onizle/', service_status_change_preview_api, name='service_status_change_preview'),
    path('services/whatsapp/durum-uygula/', service_status_change_apply_api, name='service_status_change_apply'),
    path('services/whatsapp/durum-onay/', service_whatsapp_status_confirm_api, name='service_whatsapp_status_confirm'),
    path('services/send-whatsapp/', send_services_whatsapp, name='service_send_whatsapp'),
    path('services/send-whatsapp-auto/', send_services_whatsapp_auto, name='service_send_whatsapp_auto'),

    # Settings
    path('settings/', SiteSettingsView.as_view(), name='site_settings'),
    path('profile-settings/', RedirectView.as_view(url='/profil/', permanent=False), name='profile_settings_legacy'),
    path('solution-network/', RedirectView.as_view(url='/contact/cozum-agi/', permanent=False)),
    path('personnel-network/', RedirectView.as_view(url='/contact/personel/', permanent=False)),

    # API
    path('api/settings/', settings_api, name='settings_api'),
    path('api/options/catalog/', options_catalog_api, name='options_catalog_api'),
    path('api/options/service-types/', service_types_for_products_api, name='service_types_for_products_api'),
    path('api/options/quick-create/', quick_option_create_api, name='quick_option_create_api'),
    path('api/options/quick-update/', quick_option_update_api, name='quick_option_update_api'),

    # AI (Tools'a taşındı — eski URL'ler yönlendirilir)
    path('api/ai-chat/chat/', RedirectView.as_view(url='/tools/api/ai-chat/chat/', permanent=False)),
    path('ai/panel/', RedirectView.as_view(url='/tools/ai/panel/', permanent=False), name='ai_panel'),
]
