from django.urls import include, path, re_path

from restaurant.spa_views import RestaurantSpaView

urlpatterns = [
    path('api/', include('restaurant.api.urls')),
    re_path(r'^assets/(?P<asset_path>.*)$', RestaurantSpaView.as_view(), name='restaurant_spa_assets'),
    path('', RestaurantSpaView.as_view(), name='restaurant_hub'),
    re_path(r'^(?P<spa_path>.*)$', RestaurantSpaView.as_view(), name='restaurant_spa'),
]
