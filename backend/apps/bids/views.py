"""As rotas dos lances: dar um lance e ver os meus arremates."""

from django.db.models import Max
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsBidder
from apps.auctions.models import Lot
from apps.auctions.serializers import LotSerializer
from apps.auctions.settlement import settle_if_due
from apps.auctions.views import lots_with_details

from .serializers import BidInputSerializer, BidSerializer, MyOpenBidSerializer, MyWonLotSerializer
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


class MyBidsView(APIView):
    """Meus arremates: os lotes abertos em que dei lance e os que venci."""

    permission_classes = [IsBidder]

    def get(self, request):
        user = request.user
        now = timezone.now()

        # Liquidação preguiçosa, como no place_bid: o lote que já terminou aparece como vencido.
        due = Lot.objects.filter(
            bids__bidder=user, status=Lot.Status.OPEN, ends_at__lte=now
        ).values_list("id", flat=True)
        for lot_id in set(due):
            settle_if_due(lot_id, now)

        # O filtro vem antes do annotate, então o Max olha só os lances deste licitante.
        open_lots = list(
            lots_with_details()
            .filter(status=Lot.Status.OPEN, bids__bidder=user)
            .annotate(my_max_bid=Max("bids__amount"))
            .order_by("ends_at")
        )
        won_lots = list(
            lots_with_details()
            .select_related("receipt")
            .filter(status=Lot.Status.CLOSED, winner=user)
            .order_by("-closed_at")
        )

        context = {"now": now, "user": user}
        return Response(
            {
                "bids": MyOpenBidSerializer(open_lots, many=True, context=context).data,
                "won": MyWonLotSerializer(won_lots, many=True, context=context).data,
                "counts": {"bids": len(open_lots), "won": len(won_lots)},
            }
        )
