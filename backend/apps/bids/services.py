"""O motor de lances: o único lugar do sistema que grava lances."""

from dataclasses import dataclass
from datetime import timedelta
from .events import announce_bid
from .models import GENESIS_HASH, Bid

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.auctions.models import Lot
from apps.audit.hashing import compute_bid_hash
from apps.wallet.services import get_balance
from core.exceptions import BusinessRuleError
from core.money import format_brl

from .models import GENESIS_HASH, Bid

# Anti-sniping: um lance nos últimos 2 minutos leva o fim para "horário do lance + 2 minutos".
ANTI_SNIPING_WINDOW = timedelta(minutes=2)


@dataclass(frozen=True)
class PlacedBid:
    bid: Bid
    lot: Lot
    extended: bool


def place_bid(lot_id, bidder, amount: int, now=None) -> PlacedBid:
    """Valida e grava um lance. Recusa com BusinessRuleError (422) e um código para a tela."""
    if not bidder.is_bidder:
        raise PermissionDenied("Só licitantes podem dar lances.")
    now = now or timezone.now()

    with transaction.atomic():
        # Ordem fixa das travas: primeiro o lote, depois o licitante. Assim não há deadlock.
        lot = Lot.objects.select_for_update().get(id=lot_id)
        _check_phase(lot, now)

        if lot.leader_id == bidder.id:
            raise BusinessRuleError(
                "ALREADY_WINNING",
                "Você já está ganhando este lote. Não é preciso cobrir o próprio lance.",
            )

        minimum = lot.minimum_next_bid
        if amount < minimum:
            raise BusinessRuleError(
                "BELOW_MINIMUM",
                f"Lance abaixo do mínimo. O lance mínimo agora é {format_brl(minimum)}.",
                {"minimum": minimum},
            )

        bidder = User.objects.select_for_update().get(id=bidder.id)
        available = get_balance(bidder).available
        if amount > available:
            raise BusinessRuleError(
                "INSUFFICIENT_BALANCE",
                f"Saldo insuficiente. Seu saldo disponível é {format_brl(available)}.",
                {"available": available},
            )

        bid = _record_bid(lot, bidder, amount, now)
        extended = _extend_if_sniping(lot, now)
        lot.current_price = amount
        lot.leader = bidder
        lot.bid_count = bid.sequence
        lot.last_bid_hash = bid.hash
        lot.save(update_fields=["current_price", "leader", "bid_count", "last_bid_hash", "ends_at"])
        result = PlacedBid(bid=bid, lot=lot, extended=extended)
        transaction.on_commit(lambda: announce_bid(result))

    return result


def _check_phase(lot: Lot, now) -> None:
    phase = lot.phase_at(now)
    if phase == Lot.Phase.SCHEDULED:
        opens_at = timezone.localtime(lot.starts_at).strftime("%d/%m às %H:%M")
        raise BusinessRuleError(
            "LOT_NOT_STARTED",
            f"Este lote ainda não começou. Abre em {opens_at}.",
            {"starts_at": lot.starts_at.isoformat()},
        )
    if phase != Lot.Phase.LIVE:
        raise BusinessRuleError("LOT_CLOSED", "Este lote já foi encerrado.")


def _record_bid(lot: Lot, bidder, amount: int, now) -> Bid:
    """Grava o lance como o próximo elo da cadeia de hashes do lote."""
    sequence = lot.bid_count + 1
    prev_hash = lot.last_bid_hash or GENESIS_HASH
    bid_hash = compute_bid_hash(
        lot_id=lot.id,
        sequence=sequence,
        bidder_alias=bidder.public_alias,
        amount=amount,
        created_at=now,
        prev_hash=prev_hash,
    )
    return Bid.objects.create(
        lot=lot,
        bidder=bidder,
        sequence=sequence,
        amount=amount,
        created_at=now,
        prev_hash=prev_hash,
        hash=bid_hash,
    )


def _extend_if_sniping(lot: Lot, now) -> bool:
    """Se faltam 2 minutos ou menos, o novo fim é o horário do lance + 2 minutos."""
    if lot.ends_at - now > ANTI_SNIPING_WINDOW:
        return False
    lot.ends_at = now + ANTI_SNIPING_WINDOW
    return True
