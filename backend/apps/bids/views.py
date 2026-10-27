"""A rota do lance: a porta de entrada do motor de lances pela API."""

from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsBidder
from apps.auctions.models import Lot
from apps.auctions.serializers import LotSerializer

from .serializers import BidInputSerializer, BidSerializer
from .services import place_bid


class PlaceBidView(APIView):
    """Dá um lance. As regras ficam no place_bid(); aqui só entra e sai o JSON."""

    permission_classes = [IsBidder]

    def post(self, request, lot_id):
        serializer = BidInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = place_bid(lot_id, request.user, serializer.validated_data["amount"])
        except Lot.DoesNotExist as error:
            raise NotFound("Lote não encontrado.") from error

        return Response(
            {
                "bid": BidSerializer(result.bid).data,
                "lot": LotSerializer(result.lot, context={"now": timezone.now()}).data,
                "extended": result.extended,
            },
            status=status.HTTP_201_CREATED,
        )
