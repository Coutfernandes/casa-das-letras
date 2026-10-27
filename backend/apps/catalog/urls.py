"""Endereços do catálogo, montados em /api/catalog/."""

from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.CatalogSearchView.as_view(), name="catalog-search"),
]
