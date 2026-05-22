from django.urls import path

from .admin_views import (
    AdminUserCreateView,
    AdminUserDeleteView,
    AdminUserListView,
    AdminUserUpdateView,
    RoleCreateView,
    RoleDeleteView,
    RoleListView,
    RoleUpdateView,
    SuperAdminDashboardView,
)
from .views import ProfileSettingsView, UserLoginView, UserLogoutView

urlpatterns = [
    path('profil/', ProfileSettingsView.as_view(), name='profile_settings'),
    path('giris/', UserLoginView.as_view(), name='login'),
    path('cikis/', UserLogoutView.as_view(), name='logout'),
    path('yonetim/', SuperAdminDashboardView.as_view(), name='admin_dashboard'),
    path('yonetim/roller/', RoleListView.as_view(), name='admin_roles'),
    path('yonetim/roller/yeni/', RoleCreateView.as_view(), name='admin_role_create'),
    path('yonetim/roller/<int:pk>/duzenle/', RoleUpdateView.as_view(), name='admin_role_edit'),
    path('yonetim/roller/<int:pk>/sil/', RoleDeleteView.as_view(), name='admin_role_delete'),
    path('yonetim/kullanicilar/', AdminUserListView.as_view(), name='admin_users'),
    path('yonetim/kullanicilar/yeni/', AdminUserCreateView.as_view(), name='admin_user_create'),
    path('yonetim/kullanicilar/<int:pk>/duzenle/', AdminUserUpdateView.as_view(), name='admin_user_edit'),
    path('yonetim/kullanicilar/<int:pk>/sil/', AdminUserDeleteView.as_view(), name='admin_user_delete'),
]
