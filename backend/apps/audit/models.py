"""Comprovante de arremate, compartilhável por link."""

import secrets

from django.db import models

from apps.auctions.models import Lot
from core.models import AppendOnlyModel, UUIDModel


def generate_public_token():
    """Token aleatório de 32 caracteres, impossível de adivinhar."""
    return secrets.token_urlsafe(24)


class Receipt(UUIDModel, AppendOnlyModel):
    """
    Comprovante emitido na liquidação de um lote com vencedor.

    Mostra só o pseudônimo do vencedor e guarda o hash do último lance,
    o que liga o comprovante à cadeia auditável do lote.
    """

    lot = models.OneToOneField(
        Lot, verbose_name="lote", on_delete=models.PROTECT, related_name="receipt"
    )
    public_token = models.CharField(
        "token do link público",
        max_length=43,
        unique=True,
        default=generate_public_token,
        editable=False,
    )
    winner_alias = models.CharField("pseudônimo do vencedor", max_length=40)
    amount = models.PositiveBigIntegerField("valor (centavos)")
    last_bid_hash = models.CharField("hash do último lance", max_length=64)
    issued_at = models.DateTimeField("emitido em", auto_now_add=True)

    class Meta:
        verbose_name = "comprovante"
        verbose_name_plural = "comprovantes"
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Comprovante de {self.lot}"
