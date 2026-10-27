"""Endereços WebSocket, como o urls.py faz para o HTTP."""

from django.urls import path

from .consumers import LotConsumer

websocket_urlpatterns = [
    path("ws/lots/<uuid:lot_id>/", LotConsumer.as_asgi()),
]
