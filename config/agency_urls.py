from django.urls import path

from agency.views import (
    AgencyCampaignsView,
    AgencyClientDetailView,
    AgencyClientsView,
    AgencyFinanceView,
    AgencyFirmsView,
    AgencyFreelancersView,
    AgencyHubView,
    AgencyPipelineView,
    AgencyProjectDetailView,
)

urlpatterns = [
    path('', AgencyHubView.as_view(), name='agency_hub'),
    path('proje/<int:pk>/', AgencyProjectDetailView.as_view(), name='agency_project_detail'),
    path('musteriler/', AgencyClientsView.as_view(), name='agency_clients'),
    path('musteriler/<int:pk>/', AgencyClientDetailView.as_view(), name='agency_client_detail'),
    path('freelancer/', AgencyFreelancersView.as_view(), name='agency_freelancers'),
    path('firmalar/', AgencyFirmsView.as_view(), name='agency_firms'),
    path('pipeline/', AgencyPipelineView.as_view(), name='agency_pipeline'),
    path('finans/', AgencyFinanceView.as_view(), name='agency_finance'),
    path('kampanya/', AgencyCampaignsView.as_view(), name='agency_campaigns'),
]
