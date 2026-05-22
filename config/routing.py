from django.urls import path

from .consumers import LiveSyncConsumer


websocket_urlpatterns = [
    path("ws/live-sync/", LiveSyncConsumer.as_asgi()),
]
