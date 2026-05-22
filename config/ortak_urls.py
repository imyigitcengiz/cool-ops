from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/contact/', permanent=False)),
    path('<path:rest>', RedirectView.as_view(url='/contact/%(rest)s', permanent=False)),
]
