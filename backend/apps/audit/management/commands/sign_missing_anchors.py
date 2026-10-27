"""Assina a âncora dos lotes que receberam lances antes de existir a assinatura."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.audit.anchors import push_anchor
from apps.audit.hashing import hash_of
from apps.audit.signing import sign_anchor
from apps.auctions.models import Lot
from apps.bids.models import GENESIS_HASH


def chain_is_intact(lot) -> bool:
    """Confere a cadeia de hashes do lote, do primeiro lance até a âncora gravada no lote."""
    expected_prev = GENESIS_HASH
    bids = lot.bids.select_related("bidder").order_by("sequence")
    count = 0
    for count, bid in enumerate(bids, start=1):
        if bid.sequence != count or bid.prev_hash != expected_prev or hash_of(bid) != bid.hash:
            return False
        expected_prev = bid.hash
    return count == lot.bid_count and expected_prev == lot.last_bid_hash


class Command(BaseCommand):
    help = "Assina a âncora dos lotes com lances e sem assinatura, se a cadeia de hashes estiver íntegra."

    def handle(self, *args, **options):
        pending = Lot.objects.filter(bid_count__gt=0, anchor_signature="").values_list("id", flat=True)

        signed = skipped = 0
        for lot_id in pending:
            with transaction.atomic():
                # Trava o lote: um lance que chegue agora espera, e não há assinatura velha por cima.
                lot = Lot.objects.select_for_update().get(id=lot_id)
                if lot.anchor_signature:
                    continue
                if not chain_is_intact(lot):
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f"Cadeia quebrada, não assinado: lote {lot.id} ({lot})")
                    )
                    continue
                lot.anchor_signature = sign_anchor(lot.id, lot.bid_count, lot.last_bid_hash)
                lot.save(update_fields=["anchor_signature"])
                transaction.on_commit(lambda lot=lot: push_anchor(lot))
                signed += 1

        self.stdout.write(self.style.SUCCESS(f"{signed} lote(s) assinado(s), {skipped} pulado(s)."))
