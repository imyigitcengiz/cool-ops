from django.urls import path
from .views import ai_chat_view, AIPanelView

urlpatterns = [
    path('chat/', ai_chat_view, name='ai_chat'),
    path('panel/', AIPanelView.as_view(), name='ai_panel'),
]
