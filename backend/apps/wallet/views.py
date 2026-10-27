"""Rotas da carteira do licitante."""

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsBidder

from .models import WalletEntry
from .serializers import DepositSerializer, WalletSerializer
from .services import committed_lots, deposit, get_balance

STATEMENT_SIZE = 50


def wallet_response(user, status_code=status.HTTP_200_OK):
    balance = get_balance(user)
    data = {
        "total": balance.total,
        "committed": balance.committed,
        "available": balance.available,
        "committed_lots": committed_lots(user)
        .select_related("item", "auctioneer", "leader", "winner")
        .order_by("ends_at"),
        "entries": WalletEntry.objects.filter(user=user)
        .select_related("lot__item")
        .order_by("-created_at")[:STATEMENT_SIZE],
    }
    serializer = WalletSerializer(data, context={"now": timezone.now()})
    return Response(serializer.data, status=status_code)


class WalletView(APIView):
    permission_classes = [IsBidder]

    def get(self, request):
        return wallet_response(request.user)


class DepositView(APIView):
    permission_classes = [IsBidder]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deposit(request.user, serializer.validated_data["amount"])
        return wallet_response(request.user, status.HTTP_201_CREATED)
