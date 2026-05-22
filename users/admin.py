from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Permission, Role, User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'module', 'sort_order')
    list_filter = ('module',)
    search_fields = ('name', 'codename')
    ordering = ('module', 'sort_order', 'name')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_system')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('permissions',)
    search_fields = ('name', 'slug')


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'display_name', 'email', 'role', 'is_superuser', 'is_active')
    list_filter = ('role', 'is_superuser', 'is_staff', 'is_active')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Rol', {'fields': ('role',)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Rol', {'fields': ('role',)}),
    )
    inlines = [UserProfileInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
