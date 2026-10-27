"""
A manutenção de cada minuto: liquida os lotes vencidos e repõe as âncoras atrasadas no Redis.

Usada pelo comando close_due_lots e pela rota POST /api/internal/tick/ (chamada pelo cron-job.org).
"""

from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.audit.anchors import restore_anchor

from .models import Lot
from .settlement import settle_lot

# Só os lotes com lance recente podem ter ficado para trás no Redis. Olhar só para eles
# poupa a cota do Upstash (500 mil comandos por mês): cada lote conferido gasta um comando.
RECENT_BIDS_WINDOW = timedelta(hours=24)


@dataclass(frozen=True)
class TickResult:
    settled: int
    restored: int


def run_tick(now=None) -> TickResult:
    """Liquida os lotes que já terminaram e repõe as âncoras dos lotes recentes."""
    now = now or timezone.now()
    due = list(Lot.objects.filter(status=Lot.Status.OPEN, ends_at__lte=now).values_list("id", flat=True))
    for lot_id in due:
        settle_lot(lot_id, now)

    # Repõe no Redis as âncoras que ficaram para trás (o Redis estava fora do ar num lance).
    recent = Q(bids__created_at__gte=now - RECENT_BIDS_WINDOW) | Q(id__in=due)
    lots = Lot.objects.filter(recent, bid_count__gt=0).distinct()
    restored = sum(restore_anchor(lot) for lot in lots)

    return TickResult(settled=len(due), restored=restored)
