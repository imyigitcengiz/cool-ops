from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from analytics.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('', include('users.urls')),
    path('services-dashboard/', include('config.services_dashboard_urls')),
    path('tools/', include('config.tools_urls')),
    path('sales-lead/', include('config.sales_lead_urls')),
    path('contact/', include('config.contact_urls')),
    path('crm/', include('config.crm_urls')),
    path('ortak/', include('config.ortak_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
