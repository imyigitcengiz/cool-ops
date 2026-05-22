from django.urls import path
from django.views.generic import RedirectView

from sales_leads.views import (
    SalesLeadCreateView,
    SalesLeadDashboardView,
    SalesLeadDeleteView,
    SalesLeadExportCsvView,
    SalesLeadListView,
    SalesLeadReportsView,
    SalesLeadUpdateView,
)

urlpatterns = [
    path('', SalesLeadDashboardView.as_view(), name='sales_lead_dashboard'),
    path('kayitlar/', SalesLeadListView.as_view(), name='sales_lead_list'),
    path('yeni/', SalesLeadCreateView.as_view(), name='sales_lead_create'),
    path('raporlar/', SalesLeadReportsView.as_view(), name='sales_lead_reports'),
    path('raporlar/export-csv/', SalesLeadExportCsvView.as_view(), name='sales_lead_export_csv'),

    path('musteriler/', RedirectView.as_view(url='/contact/musteriler/', permanent=False)),
    path('musteriler/<path:rest>', RedirectView.as_view(url='/contact/musteriler/%(rest)s', permanent=False)),

    path('<int:pk>/duzenle/', SalesLeadUpdateView.as_view(), name='sales_lead_edit'),
    path('<int:pk>/sil/', SalesLeadDeleteView.as_view(), name='sales_lead_delete'),
]
