"""Endereços da carteira, montados em /api/wallet/."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.WalletView.as_view(), name="wallet"),
    path("deposit/", views.DepositView.as_view(), name="wallet-deposit"),
]
