"""Endereços do comprovante e da auditoria, montados em /api/ pelo core/urls.py."""

from django.urls import path

from . import views

urlpatterns = [
    path("receipts/<str:token>/", views.ReceiptView.as_view(), name="receipt-detail"),
    path("audit/lots/<uuid:lot_id>/", views.AuditLotView.as_view(), name="audit-lot"),
    path("audit/public-key/", views.PublicKeyView.as_view(), name="audit-public-key"),
]
