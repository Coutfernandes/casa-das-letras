"""Lances dados nos lotes."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.auctions.models import Lot
from core.models import AppendOnlyModel, UUIDModel

# Valor de prev_hash do primeiro lance de cada lote.
GENESIS_HASH = "GENESIS"


class Bid(UUIDModel, AppendOnlyModel):
    """
    Um lance aceito, elo da cadeia de hashes do lote.

    Cada lance guarda o hash do anterior (prev_hash) e o próprio (hash).
    O cálculo e a verificação ficam em apps/audit (seção 7 da spec).
    """

    lot = models.ForeignKey(Lot, verbose_name="lote", on_delete=models.PROTECT, related_name="bids")
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="licitante",
        on_delete=models.PROTECT,
        related_name="bids",
    )
    sequence = models.PositiveIntegerField("número do lance no lote")
    amount = models.PositiveBigIntegerField("valor (centavos)")
    created_at = models.DateTimeField("dado em", default=timezone.now, editable=False)
    prev_hash = models.CharField("hash do lance anterior", max_length=64)
    hash = models.CharField("hash", max_length=64, unique=True)

    class Meta:
        verbose_name = "lance"
        verbose_name_plural = "lances"
        ordering = ["lot", "sequence"]
        constraints = [
            models.UniqueConstraint(fields=["lot", "sequence"], name="bid_unique_sequence_per_lot"),
            models.CheckConstraint(condition=models.Q(sequence__gte=1), name="bid_sequence_positive"),
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="bid_amount_positive"),
        ]

    def __str__(self):
        return f"Lance #{self.sequence} em {self.lot}"