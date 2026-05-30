from django.contrib import admin

from agency.models import (
    AgencyCampaign,
    AgencyClient,
    AgencyDeal,
    AgencyDeliverable,
    AgencyFinanceEntry,
    AgencyFirm,
    AgencyFreelancer,
    AgencyProject,
    AgencyProjectAssignment,
)


@admin.register(AgencyDeliverable)
class AgencyDeliverableAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'due_date', 'is_done')
    list_filter = ('is_done',)


@admin.register(AgencyProjectAssignment)
class AgencyProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ('project', 'freelancer', 'role_label', 'hours_budget')


@admin.register(AgencyClient)
class AgencyClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'contract_type', 'phone', 'email')
    search_fields = ('name', 'contact_name')


@admin.register(AgencyFreelancer)
class AgencyFreelancerAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'hourly_rate', 'is_active')
    list_filter = ('is_active',)


@admin.register(AgencyFirm)
class AgencyFirmAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'status')
    list_filter = ('status',)


@admin.register(AgencyProject)
class AgencyProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'status', 'monthly_retainer', 'owner')
    list_filter = ('status',)


@admin.register(AgencyDeal)
class AgencyDealAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'stage', 'amount')
    list_filter = ('stage',)


@admin.register(AgencyFinanceEntry)
class AgencyFinanceEntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'amount', 'entry_date')
    list_filter = ('kind',)


@admin.register(AgencyCampaign)
class AgencyCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'target_client')
    list_filter = ('status',)
