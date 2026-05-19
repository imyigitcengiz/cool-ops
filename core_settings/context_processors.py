from .models import WhatsAppTemplate, SiteSettings

def whatsapp_context(request):
    return {
        'whatsapp_templates': WhatsAppTemplate.objects.all()
    }

def site_settings(request):
    return {
        'site_settings': SiteSettings.objects.first()
    }
