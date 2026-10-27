"""Os eventos que a sala do lote recebe pelo WebSocket."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from apps.auctions.serializers import LotSerializer

from .models import Bid
from .serializers import BidSerializer

logger = logging.getLogger(__name__)

RECENT_BIDS = 20


def lot_group(lot_id) -> str:
    """O nome do grupo de todas as conexões abertas num lote."""
    return f"lot.{lot_id}"


def _lot_data(lot, now) -> dict:
    return LotSerializer(lot, context={"now": now}).data


def lot_snapshot(lot) -> dict:
    """O estado completo da sala, enviado a quem acabou de conectar."""
    now = timezone.now()
    bids = Bid.objects.filter(lot=lot).select_related("bidder").order_by("-sequence")[:RECENT_BIDS]
    return {
        "type": "lot.snapshot",
        "lot": _lot_data(lot, now),
        "bids": BidSerializer(bids, many=True).data,
        "server_now": now.isoformat(),
    }


def broadcast(lot_id, payload: dict) -> None:
    """Manda um evento a todas as conexões abertas no lote. Uma falha aqui nunca desfaz um lance."""
    try:
        async_to_sync(get_channel_layer().group_send)(
            lot_group(lot_id), {"type": "lot.event", "payload": payload}
        )
    except Exception:
        logger.exception("Não foi possível avisar a sala do lote %s", lot_id)


def announce_bid(placed) -> None:
    """Avisa a sala de um lance aceito e, se houve anti-sniping, do novo fim."""
    now = timezone.now()
    lot = placed.lot
    broadcast(
        lot.id,
        {
            "type": "bid.accepted",
            "bid": BidSerializer(placed.bid).data,
            "lot": _lot_data(lot, now),
            "server_now": now.isoformat(),
        },
    )
    if placed.extended:
        broadcast(
            lot.id,
            {
                "type": "lot.extended",
                "ends_at": lot.ends_at.isoformat(),
                "original_ends_at": lot.original_ends_at.isoformat(),
                "server_now": now.isoformat(),
            },
        )


def announce_cancellation(lot) -> None:
    """Avisa a sala de que o leiloeiro cancelou o lote."""
    now = timezone.now()
    broadcast(
        lot.id,
        {
            "type": "lot.cancelled",
            "reason": "Lote cancelado pelo leiloeiro.",
            "lot": _lot_data(lot, now),
            "server_now": now.isoformat(),
        },
    )