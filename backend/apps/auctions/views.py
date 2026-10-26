"""Rotas dos lotes: vitrine e detalhe (públicas) e painel do leiloeiro."""

from django.db.models import Q, Sum, TextField
from django.db.models.functions import Cast, Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAuctioneer
from apps.catalog.open_library import CatalogBook
from apps.wallet.models import WalletEntry

from .models import Lot
from .serializers import LotCreateSerializer, LotFilterSerializer, LotSerializer
from .services import LotTerms, cancel_lot, create_lot

PHASES = ("live", "scheduled", "finished")

# Ordem de cada aba da vitrine: o que termina, começa ou terminou mais perto vem primeiro.
PHASE_ORDERING = {
    "live": ["ends_at"],
    "scheduled": ["starts_at"],
    "finished": ["-ends_at"],
}


def lots_with_details():
    """Lotes já com livro, leiloeiro, líder e vencedor, numa consulta só."""
    return Lot.objects.select_related("item", "auctioneer", "leader", "winner")


def filter_lots(lots, filters):
    """Aplica a busca por título ou autor e a faixa de preço da vitrine."""
    if filters.get("q"):
        term = filters["q"]
        lots = lots.annotate(authors_text=Cast("item__authors", TextField())).filter(
            Q(item__title__icontains=term) | Q(authors_text__icontains=term)
        )
    if "min_price" in filters or "max_price" in filters:
        lots = lots.annotate(price=Coalesce("current_price", "starting_price"))
        if "min_price" in filters:
            lots = lots.filter(price__gte=filters["min_price"])
        if "max_price" in filters:
            lots = lots.filter(price__lte=filters["max_price"])
    return lots


class LotListView(APIView):
    """A vitrine. Pública: qualquer pessoa vê os lotes, mesmo sem login."""

    permission_classes = [AllowAny]

    def get(self, request):
        filters = LotFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        phase = filters.validated_data["phase"]
        now = timezone.now()

        visible = Lot.objects.visible()
        counts = {name: getattr(visible, name)(now).count() for name in PHASES}

        lots = getattr(lots_with_details().visible(), phase)(now)
        lots = filter_lots(lots, filters.validated_data).order_by(*PHASE_ORDERING[phase])

        return Response(
            {
                "counts": counts,
                "results": LotSerializer(lots, many=True, context={"now": now}).data,
            }
        )


class LotDetailView(APIView):
    """Um lote. Público, como a vitrine."""

    permission_classes = [AllowAny]

    def get(self, request, lot_id):
        lot = get_object_or_404(lots_with_details(), id=lot_id)
        return Response(LotSerializer(lot, context={"now": timezone.now()}).data)


class AuctioneerLotsView(APIView):
    """Painel do leiloeiro: os próprios lotes, o resumo e a criação de lotes."""

    permission_classes = [IsAuctioneer]

    def get(self, request):
        now = timezone.now()
        lots = list(lots_with_details().filter(auctioneer=request.user).order_by("-created_at"))

        phases = [lot.phase_at(now) for lot in lots]
        total_received = WalletEntry.objects.filter(
            user=request.user, kind=WalletEntry.Kind.SETTLEMENT_CREDIT
        ).aggregate(total=Sum("amount"))["total"]

        return Response(
            {
                "summary": {
                    "live": phases.count(Lot.Phase.LIVE),
                    "scheduled": phases.count(Lot.Phase.SCHEDULED),
                    "finished": phases.count(Lot.Phase.CLOSED) + phases.count(Lot.Phase.ENDED),
                    "total_received": total_received or 0,
                },
                "results": LotSerializer(lots, many=True, context={"now": now}).data,
            }
        )

    def post(self, request):
        serializer = LotCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)

        book = CatalogBook(**data.pop("book"))
        lot = create_lot(request.user, book, LotTerms(**data))

        lot = lots_with_details().get(id=lot.id)
        return Response(
            LotSerializer(lot, context={"now": timezone.now()}).data,
            status=status.HTTP_201_CREATED,
        )


class AuctioneerLotCancelView(APIView):
    """Cancela um lote do leiloeiro que ainda não recebeu lances."""

    permission_classes = [IsAuctioneer]

    def post(self, request, lot_id):
        try:
            cancel_lot(lot_id, request.user)
        except Lot.DoesNotExist as error:
            raise NotFound("Lote não encontrado.") from error

        lot = lots_with_details().get(id=lot_id)
        return Response(LotSerializer(lot, context={"now": timezone.now()}).data)