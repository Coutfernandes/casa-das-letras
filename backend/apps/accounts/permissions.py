"""Permissões por papel, usadas nas rotas de leiloeiro e de licitante."""

from rest_framework.permissions import BasePermission


class IsAuctioneer(BasePermission):
    """Só leiloeiros: criar, cancelar e acompanhar os próprios lotes."""

    message = "Apenas leiloeiros podem fazer isso."

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.is_auctioneer


class IsBidder(BasePermission):
    """Só licitantes: dar lances e usar a carteira."""

    message = "Apenas licitantes podem dar lances e usar a carteira."

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.is_bidder