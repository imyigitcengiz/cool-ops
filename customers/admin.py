from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'region', 'created_at')
    search_fields = ('name', 'phone', 'region')
    list_filter = ('region',)
