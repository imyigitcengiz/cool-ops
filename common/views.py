from django.views.generic import TemplateView


class ContactHubView(TemplateView):
    template_name = 'crm/index.html'


class CrmHubView(ContactHubView):
    """Geriye dönük uyumluluk."""


class OrtakHubView(CrmHubView):
    """Geriye dönük uyumluluk."""
