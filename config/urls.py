from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from analytics.views import DashboardView
from services.views import (
    ServiceListView, ServiceCreateView, ServiceUpdateView, ServiceDeleteView, 
    ServicePrintView, ServiceBulkPrintView, bulk_delete_services, send_services_whatsapp, send_services_whatsapp_auto,
    quick_update_service_field, service_quick_edit_api, bulk_manage_services, restore_service_history_entry
)
from customers.views import (
    CustomerListView, CustomerCreateView, CustomerUpdateView, CustomerDeleteView, 
    bulk_delete_customers, quick_customer_create, customer_detail_api, update_customer_products, customer_quick_edit_api,
    bulk_manage_customers
)
from core_settings.views import (
    SiteSettingsView,
    ProfileSettingsView,
    SolutionNetworkView,
    PersonnelNetworkView,
    settings_api,
    options_catalog_api,
    service_types_for_products_api,
    quick_option_create_api,
    quick_option_update_api,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    
    # Services
    path('services/', ServiceListView.as_view(), name='services'),
    path('services/new/', ServiceCreateView.as_view(), name='service_create'),
    path('services/<int:pk>/edit/', ServiceUpdateView.as_view(), name='service_update'),
    path('services/<int:pk>/delete/', ServiceDeleteView.as_view(), name='service_delete'),
    path('services/<int:pk>/print/', ServicePrintView.as_view(), name='service_print'),
    path('services/<int:pk>/quick-edit/', service_quick_edit_api, name='service_quick_edit_api'),
    path('services/<int:pk>/history/<int:history_id>/restore/', restore_service_history_entry, name='service_restore_history'),
    path('services/bulk-print/', ServiceBulkPrintView.as_view(), name='service_bulk_print'),
    path('services/bulk-delete/', bulk_delete_services, name='service_bulk_delete'),
    path('services/bulk-manage/', bulk_manage_services, name='service_bulk_manage'),
    path('services/quick-update/', quick_update_service_field, name='service_quick_update'),
    path('services/send-whatsapp/', send_services_whatsapp, name='service_send_whatsapp'),
    path('services/send-whatsapp-auto/', send_services_whatsapp_auto, name='service_send_whatsapp_auto'),
    
    # Customers
    path('customers/', CustomerListView.as_view(), name='customers'),
    path('customers/new/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),
    path('customers/bulk-delete/', bulk_delete_customers, name='customer_bulk_delete'),
    path('customers/bulk-manage/', bulk_manage_customers, name='customer_bulk_manage'),
    path('customers/quick-add/', quick_customer_create, name='customer_quick_add'),
    path('customers/api/<int:pk>/', customer_detail_api, name='customer_detail_api'),
    path('customers/api/<int:pk>/update-products/', update_customer_products, name='update_customer_products'),
    path('customers/<int:pk>/quick-edit/', customer_quick_edit_api, name='customer_quick_edit_api'),
    
    # Settings
    path('settings/', SiteSettingsView.as_view(), name='site_settings'),
    path('profile-settings/', ProfileSettingsView.as_view(), name='profile_settings'),
    path('solution-network/', SolutionNetworkView.as_view(), name='solution_network'),
    path('personnel-network/', PersonnelNetworkView.as_view(), name='personnel_network'),
    # Settings API
    path('api/settings/', settings_api, name='settings_api'),
    path('api/options/catalog/', options_catalog_api, name='options_catalog_api'),
    path('api/options/service-types/', service_types_for_products_api, name='service_types_for_products_api'),
    path('api/options/quick-create/', quick_option_create_api, name='quick_option_create_api'),
    path('api/options/quick-update/', quick_option_update_api, name='quick_option_update_api'),
    
    # AI API
    path('api/ai-chat/', include([
        path('', include('analytics.urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
