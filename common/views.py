from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView


@require_GET
def healthz(request):
    """Docker / Traefik sağlık kontrolü — auth yok, DB yok."""
    return HttpResponse('ok', content_type='text/plain')


class ContactHubView(TemplateView):
    template_name = 'crm/index.html'

    def get_context_data(self, **kwargs):
        from customers.customer_overview import build_rehber_hub_stats

        context = super().get_context_data(**kwargs)
        context.update(build_rehber_hub_stats())
        return context


class CrmHubView(ContactHubView):
    """Geriye dönük uyumluluk."""


class OrtakHubView(CrmHubView):
    """Geriye dönük uyumluluk."""


class IntroducerKnowledgeBaseView(TemplateView):
    """Tanıtım yapan kullanıcılar için yol haritası ve modül rehberi — giriş gerekmez."""

    template_name = 'knowledge_bank/index.html'

    def get_context_data(self, **kwargs):
        from common.introducer_bank import build_introducer_context, get_journey

        context = super().get_context_data(**kwargs)
        context.update(build_introducer_context())
        slug = self.request.GET.get('yol', '').strip()
        context['active_journey'] = get_journey(slug)
        context['active_journey_slug'] = context['active_journey']['slug'] if context['active_journey'] else ''
        return context
