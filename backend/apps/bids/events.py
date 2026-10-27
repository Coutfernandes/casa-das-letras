"""Os eventos que a sala do lote recebe pelo WebSocket."""

from django.utils import timezone

from apps.auctions.serializers import LotSerializer

from .models import Bid
from .serializers import BidSerializer

RECENT_BIDS = 20


def lot_group(lot_id) -> str:
    """O nome do grupo de todas as conexões abertas num lote."""
    return f"lot.{lot_id}"


def lot_snapshot(lot) -> dict:
    """O estado completo da sala, enviado a quem acabou de conectar."""
    now = timezone.now()
    bids = Bid.objects.filter(lot=lot).select_related("bidder").order_by("-sequence")[:RECENT_BIDS]
    return {
        "type": "lot.snapshot",
        "lot": LotSerializer(lot, context={"now": now}).data,
        "bids": BidSerializer(bids, many=True).data,
        "server_now": now.isoformat(),
    }
