"""Endereço do comprovante, montado em /api/ pelo core/urls.py."""

from django.urls import path

from . import views

urlpatterns = [
    path("receipts/<str:token>/", views.ReceiptView.as_view(), name="receipt-detail"),
]
