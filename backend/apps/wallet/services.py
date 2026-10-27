"""Saldo da carteira: total, comprometido e disponível, sempre calculados."""

from dataclasses import dataclass

from django.db.models import Sum

from apps.auctions.models import Lot
from core.exceptions import BusinessRuleError

from .models import WalletEntry

# Limite de um depósito simulado, em centavos: R$ 100.000,00.
MAX_DEPOSIT = 100_000_00

FINAL_STATUSES = (Lot.Status.CLOSED, Lot.Status.CANCELLED)


@dataclass(frozen=True)
class Balance:
    total: int
    committed: int

    @property
    def available(self) -> int:
        return self.total - self.committed


def committed_lots(user):
    """Lotes que o licitante lidera e que ainda não foram liquidados nem cancelados."""
    return Lot.objects.filter(leader=user).exclude(status__in=FINAL_STATUSES)


def get_balance(user) -> Balance:
    total = WalletEntry.objects.filter(user=user).aggregate(total=Sum("amount"))["total"]
    committed = committed_lots(user).aggregate(total=Sum("current_price"))["total"]
    return Balance(total=total or 0, committed=committed or 0)


def deposit(user, amount: int) -> WalletEntry:
    """Depósito simulado: só cria uma entrada positiva na carteira."""
    if not user.is_bidder:
        raise BusinessRuleError("NOT_BIDDER", "Só licitantes têm carteira.")
    if not 0 < amount <= MAX_DEPOSIT:
        raise BusinessRuleError(
            "INVALID_DEPOSIT",
            "O depósito precisa ser maior que zero e de no máximo R$ 100.000,00.",
            {"max_amount": MAX_DEPOSIT},
        )
    return WalletEntry.objects.create(user=user, kind=WalletEntry.Kind.DEPOSIT, amount=amount)
