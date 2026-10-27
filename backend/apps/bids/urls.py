"""Endereços dos lances, montados em /api/ pelo core/urls.py."""

from django.urls import path

from . import views

urlpatterns = [
    path("lots/<uuid:lot_id>/bids/", views.PlaceBidView.as_view(), name="lot-bids"),
    path("me/bids/", views.MyBidsView.as_view(), name="my-bids"),
]
