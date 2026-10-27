"""Rota do comprovante público de arremate."""

from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Receipt
from .serializers import ReceiptSerializer


class ReceiptView(APIView):
    """Um comprovante, aberto por quem tiver o link. Não precisa de login."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        receipt = get_object_or_404(
            Receipt.objects.select_related("lot__item", "lot__auctioneer"), public_token=token
        )
        return Response(ReceiptSerializer(receipt).data)
