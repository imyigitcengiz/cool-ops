from django.contrib import admin

from restaurant.models import (
    RestaurantAuditLog,
    RestaurantBranch,
    RestaurantCashRegister,
    RestaurantCashTransaction,
    RestaurantCategory,
    RestaurantCourier,
    RestaurantCourierLog,
    RestaurantCustomer,
    RestaurantExpense,
    RestaurantFranchisePanelToken,
    RestaurantIngredient,
    RestaurantMenuItem,
    RestaurantMenuItemModifier,
    RestaurantOrder,
    RestaurantOrderChannel,
    RestaurantOrderItem,
    RestaurantPayment,
    RestaurantProfile,
    RestaurantRecipe,
    RestaurantRecipeIngredient,
    RestaurantStaffMember,
    RestaurantStockAudit,
    RestaurantStockAuditItem,
    RestaurantSubscriptionInvoice,
    RestaurantTable,
    RestaurantTenantProfile,
    RestaurantWhatsAppConfig,
)


@admin.register(RestaurantTenantProfile)
class RestaurantTenantProfileAdmin(admin.ModelAdmin):
    list_display = ('brand', 'plan_tier', 'plan_expiry', 'public_slug')


@admin.register(RestaurantCategory)
class RestaurantCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'is_active')
    list_filter = ('brand',)


@admin.register(RestaurantMenuItem)
class RestaurantMenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'is_available')
    list_filter = ('brand',)


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'branch', 'status', 'capacity')
    list_filter = ('brand', 'status')


admin.site.register(RestaurantMenuItemModifier)
admin.site.register(RestaurantBranch)
admin.site.register(RestaurantOrder)
admin.site.register(RestaurantOrderItem)
admin.site.register(RestaurantPayment)
admin.site.register(RestaurantOrderChannel)
admin.site.register(RestaurantCashRegister)
admin.site.register(RestaurantIngredient)
admin.site.register(RestaurantRecipe)
admin.site.register(RestaurantRecipeIngredient)
admin.site.register(RestaurantStaffMember)
admin.site.register(RestaurantExpense)
admin.site.register(RestaurantCourier)
admin.site.register(RestaurantCourierLog)
admin.site.register(RestaurantProfile)
admin.site.register(RestaurantCashTransaction)
admin.site.register(RestaurantStockAudit)
admin.site.register(RestaurantStockAuditItem)
admin.site.register(RestaurantCustomer)
admin.site.register(RestaurantWhatsAppConfig)
admin.site.register(RestaurantFranchisePanelToken)
admin.site.register(RestaurantAuditLog)
admin.site.register(RestaurantSubscriptionInvoice)
