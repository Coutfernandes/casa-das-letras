"""Endereço do lance, montado em /api/ pelo core/urls.py."""

from django.urls import path

from . import views

urlpatterns = [
    path("lots/<uuid:lot_id>/bids/", views.PlaceBidView.as_view(), name="lot-bids"),
]
