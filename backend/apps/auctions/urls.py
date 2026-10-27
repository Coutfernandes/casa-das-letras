"""Endereços dos lotes, montados em /api/ pelo core/urls.py."""

from django.urls import path

from . import views

urlpatterns = [
    path("lots/", views.LotListView.as_view(), name="lot-list"),
    path("lots/<uuid:lot_id>/", views.LotDetailView.as_view(), name="lot-detail"),
    path("auctioneer/lots/", views.AuctioneerLotsView.as_view(), name="auctioneer-lots"),
    path(
        "auctioneer/lots/<uuid:lot_id>/cancel/",
        views.AuctioneerLotCancelView.as_view(),
        name="auctioneer-lot-cancel",
    ),
]
