from django.contrib import admin

from .models import SalesLead, SalesLeadInterimPayment, SalesLeadProductLine


class SalesLeadInterimPaymentInline(admin.TabularInline):
    model = SalesLeadInterimPayment
    extra = 0


class SalesLeadProductLineInline(admin.TabularInline):
    model = SalesLeadProductLine
    extra = 0


@admin.register(SalesLead)
class SalesLeadAdmin(admin.ModelAdmin):
    list_display = ('customer', 'sale_date', 'sale_amount', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'sale_date', 'assigned_to')
    search_fields = ('customer__name', 'customer__phone', 'notes', 'project')
    raw_id_fields = ('customer', 'assigned_to')
    inlines = [SalesLeadInterimPaymentInline, SalesLeadProductLineInline]