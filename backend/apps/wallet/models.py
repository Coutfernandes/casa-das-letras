"""Carteira simulada: o extrato de entradas e saídas de cada usuário."""

from django.conf import settings
from django.db import models

from apps.auctions.models import Lot
from core.models import AppendOnlyModel, UUIDModel


class WalletEntry(UUIDModel, AppendOnlyModel):
    """
    Uma linha do extrato. O saldo total é a soma de todas as linhas do usuário.

    O saldo comprometido não é gravado: é calculado a partir dos lances em que
    o usuário lidera (seção 6 da spec).
    """

    class Kind(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Depósito simulado"
        SETTLEMENT_DEBIT = "SETTLEMENT_DEBIT", "Débito de arremate"
        SETTLEMENT_CREDIT = "SETTLEMENT_CREDIT", "Crédito de venda"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuário",
        on_delete=models.PROTECT,
        related_name="wallet_entries",
    )
    kind = models.CharField("tipo", max_length=20, choices=Kind.choices)
    # Com sinal: positivo entra na carteira, negativo sai.
    amount = models.BigIntegerField("valor (centavos)")
    lot = models.ForeignKey(
        Lot,
        verbose_name="lote",
        on_delete=models.PROTECT,
        related_name="wallet_entries",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("registrado em", auto_now_add=True)

    class Meta:
        verbose_name = "movimentação"
        verbose_name_plural = "movimentações"
        ordering = ["-created_at"]
        constraints = [
            # Depósitos e créditos entram (positivo); débitos saem (negativo).
            models.CheckConstraint(
                condition=(
                    models.Q(kind="DEPOSIT", amount__gt=0)
                    | models.Q(kind="SETTLEMENT_CREDIT", amount__gt=0)
                    | models.Q(kind="SETTLEMENT_DEBIT", amount__lt=0)
                ),
                name="wallet_entry_sign_matches_kind",
            ),
            # Movimentações de arremate sempre apontam para o lote.
            models.CheckConstraint(
                condition=models.Q(kind="DEPOSIT") | models.Q(lot__isnull=False),
                name="wallet_entry_settlement_has_lot",
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.amount} centavos"
