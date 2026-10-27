"""A liquidação do lote: quem venceu paga, o leiloeiro recebe, e sai o comprovante."""

from django.db import transaction
from django.utils import timezone

from apps.audit.models import Receipt
from apps.bids.events import announce_closed
from apps.wallet.models import WalletEntry

from .models import Lot


def settle_lot(lot_id, now=None) -> Lot:
    """
    Encerra um lote que já passou do fim. É idempotente: liquidar de novo não faz nada.
    Lotes cancelados, já liquidados ou que ainda não terminaram ficam como estão.
    """
    now = now or timezone.now()
    with transaction.atomic():
        lot = Lot.objects.select_for_update().get(id=lot_id)
        if lot.status != Lot.Status.OPEN or lot.ends_at > now:
            return lot

        lot.status = Lot.Status.CLOSED
        lot.closed_at = now
        if lot.leader is not None:
            _pay(lot, now)
        lot.save(update_fields=["status", "closed_at", "winner", "final_price"])
        transaction.on_commit(lambda: announce_closed(lot))
    return lot


def settle_if_due(lot_id, now=None) -> bool:
    """Liquida o lote se ele já passou do fim e ainda está aberto. Diz se liquidou."""
    now = now or timezone.now()
    due = Lot.objects.filter(id=lot_id, status=Lot.Status.OPEN, ends_at__lte=now).exists()
    if due:
        settle_lot(lot_id, now)
    return due


def _pay(lot: Lot, now) -> None:
    """O vencedor paga, o leiloeiro recebe, e o comprovante liga tudo à cadeia de lances."""
    price = lot.current_price
    lot.winner = lot.leader
    lot.final_price = price
    WalletEntry.objects.create(
        user=lot.leader, kind=WalletEntry.Kind.SETTLEMENT_DEBIT, amount=-price, lot=lot
    )
    WalletEntry.objects.create(
        user_id=lot.auctioneer_id, kind=WalletEntry.Kind.SETTLEMENT_CREDIT, amount=price, lot=lot
    )
    Receipt.objects.create(
        lot=lot,
        winner_alias=lot.leader.public_alias,
        amount=price,
        last_bid_hash=lot.last_bid_hash,
        issued_at=now,
    )
