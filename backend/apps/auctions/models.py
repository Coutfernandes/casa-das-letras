"""Lotes do leilão."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.catalog.models import CatalogItemSnapshot
from core.models import UUIDModel


class Lot(UUIDModel):
    """
    Um livro à venda, com preço inicial, incremento e período de lances.

    Valores em dinheiro são inteiros em centavos: R$ 1.250,00 = 125000.
    """

    class Status(models.TextChoices):
        """Estado gravado no banco. Agendado e ao vivo vêm do relógio (phase_at)."""

        OPEN = "OPEN", "Aberto"
        CLOSED = "CLOSED", "Encerrado"
        CANCELLED = "CANCELLED", "Cancelado"

    class Phase(models.TextChoices):
        """Fase do lote num instante, calculada a partir do status e das datas."""

        SCHEDULED = "SCHEDULED", "Agendado"
        LIVE = "LIVE", "Ao vivo"
        ENDED = "ENDED", "Aguardando liquidação"
        CLOSED = "CLOSED", "Encerrado"
        CANCELLED = "CANCELLED", "Cancelado"

    # Quem vende e o quê.
    auctioneer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="leiloeiro",
        on_delete=models.PROTECT,
        related_name="auctioned_lots",
        limit_choices_to={"role": "AUCTIONEER"},
    )
    item = models.OneToOneField(
        CatalogItemSnapshot,
        verbose_name="livro",
        on_delete=models.PROTECT,
        related_name="lot",
    )
    description = models.TextField("descrição do leiloeiro", max_length=1000, blank=True)

    # Regras de preço (centavos).
    starting_price = models.PositiveBigIntegerField("lance inicial (centavos)")
    min_increment = models.PositiveBigIntegerField("incremento mínimo (centavos)")

    # Período. O ends_at muda com o anti-sniping; o original fica guardado.
    starts_at = models.DateTimeField("início")
    ends_at = models.DateTimeField("fim")
    original_ends_at = models.DateTimeField("fim original", editable=False)

    status = models.CharField(
        "status", max_length=10, choices=Status.choices, default=Status.OPEN
    )

    # Situação atual do leilão, atualizada a cada lance aceito.
    current_price = models.PositiveBigIntegerField(
        "lance atual (centavos)", null=True, blank=True
    )
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="licitante na liderança",
        on_delete=models.PROTECT,
        related_name="leading_lots",
        null=True,
        blank=True,
    )

    # Âncora da auditoria (seção 7 da especificação).
    bid_count = models.PositiveIntegerField("número de lances", default=0)
    last_bid_hash = models.CharField("hash do último lance", max_length=64, blank=True)
    anchor_signature = models.CharField("assinatura da âncora", max_length=128, blank=True)

    # Resultado, preenchido na liquidação.
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="vencedor",
        on_delete=models.PROTECT,
        related_name="won_lots",
        null=True,
        blank=True,
    )
    final_price = models.PositiveBigIntegerField(
        "valor final (centavos)", null=True, blank=True
    )
    closed_at = models.DateTimeField("encerrado em", null=True, blank=True)

    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "lote"
        verbose_name_plural = "lotes"
        ordering = ["ends_at"]
        indexes = [
            # Usado para achar lotes abertos que já passaram do fim (liquidação).
            models.Index(fields=["status", "ends_at"], name="lot_status_ends_at_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")),
                name="lot_ends_after_start",
            ),
            models.CheckConstraint(
                condition=models.Q(starting_price__gt=0),
                name="lot_starting_price_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(min_increment__gt=0),
                name="lot_min_increment_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["OPEN", "CLOSED", "CANCELLED"]),
                name="lot_status_valid",
            ),
        ]

    def __str__(self):
        return self.item.title

    def save(self, *args, **kwargs):
        if self._state.adding and not self.original_ends_at:
            self.original_ends_at = self.ends_at
        super().save(*args, **kwargs)

    def phase_at(self, now=None):
        """Fase do lote no instante `now` (agora, se não for informado)."""
        now = now or timezone.now()
        if self.status == self.Status.CANCELLED:
            return self.Phase.CANCELLED
        if self.status == self.Status.CLOSED:
            return self.Phase.CLOSED
        if now < self.starts_at:
            return self.Phase.SCHEDULED
        if now < self.ends_at:
            return self.Phase.LIVE
        return self.Phase.ENDED

    @property
    def minimum_next_bid(self):
        """Menor lance aceito agora: o inicial ou o atual mais o incremento."""
        if self.current_price is None:
            return self.starting_price
        return self.current_price + self.min_increment