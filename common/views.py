from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView


@require_GET
def healthz(request):
    """Docker / Traefik sağlık kontrolü — auth yok, DB yok."""
    return HttpResponse('ok', content_type='text/plain')


def page_not_found(request, exception=None):
    return render(
        request,
        'errors/404.html',
        {'request_path': request.path},
        status=404,
    )


def permission_denied(request, exception=None):
    detail = ''
    if exception is not None:
        detail = getattr(exception, 'args', [None])[0] or str(exception)
    return render(
        request,
        'errors/403.html',
        {'exception': detail},
        status=403,
    )


def bad_request(request, exception=None):
    detail = ''
    if exception is not None:
        detail = getattr(exception, 'args', [None])[0] or str(exception)
    return render(
        request,
        'errors/400.html',
        {'error_message': detail},
        status=400,
    )


def server_error(request):
    return render(request, 'errors/500.html', status=500)


def csrf_failure(request, reason=''):
    return render(
        request,
        'errors/403.html',
        {
            'exception': (
                'Oturum doğrulaması başarısız oldu. '
                'Sayfayı yenileyip işlemi tekrar deneyin.'
            ),
        },
        status=403,
    )


class ContactHubView(TemplateView):
    template_name = 'crm/index.html'

    def get_context_data(self, **kwargs):
        from customers.customer_overview import build_rehber_hub_stats

        context = super().get_context_data(**kwargs)
        context.update(build_rehber_hub_stats(self.request))
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
        from common.panel_registry import PANEL_KOBIPOS, panel_url

        context['kobipos_panel_url'] = panel_url(PANEL_KOBIPOS)
        return context
