from django.contrib import admin
from .models import ServiceRecord, ServiceImage, ServiceHistory

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1

class ServiceHistoryInline(admin.TabularInline):
    model = ServiceHistory
    readonly_fields = ('user', 'action', 'created_at')
    extra = 0

@admin.register(ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    list_display = ('customer', 'get_products', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('customer__name', 'notes')
    inlines = [ServiceImageInline, ServiceHistoryInline]

    def get_products(self, obj):
        return ", ".join([p.name for p in obj.products.all()])
    get_products.short_description = 'Ürünler'
