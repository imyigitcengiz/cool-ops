from .models import SiteSettings


def whatsapp_context(request):
    return {}


def site_settings(request):
    try:
        settings = SiteSettings.objects.first()
    except Exception:
        settings = None
    return {'site_settings': settings}
