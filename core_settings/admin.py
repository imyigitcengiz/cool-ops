from django.contrib import admin
from .models import (
    SiteSettings,
    ServiceTypeOption,
    ProductOption,
    StatusOption,
    PriorityOption,
    WhatsAppTemplate,
    SolutionPartner,
    SolutionPartnerType,
    ServiceTeam,
    ServicePersonnel,
)

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

admin.site.register(ServiceTypeOption)
admin.site.register(ProductOption)
admin.site.register(StatusOption)
admin.site.register(PriorityOption)
admin.site.register(WhatsAppTemplate)
admin.site.register(SolutionPartner)
admin.site.register(SolutionPartnerType)
admin.site.register(ServiceTeam)
admin.site.register(ServicePersonnel)
