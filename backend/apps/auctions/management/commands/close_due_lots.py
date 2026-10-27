"""Liquida os lotes que já passaram do fim e que ninguém acessou. Em produção, roda a cada minuto."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.auctions.models import Lot
from apps.auctions.settlement import settle_lot
from apps.audit.anchors import restore_anchor


class Command(BaseCommand):
    help = "Liquida os lotes que já terminaram e ainda estão abertos."

    def handle(self, *args, **options):
        now = timezone.now()
        due = Lot.objects.filter(status=Lot.Status.OPEN, ends_at__lte=now).values_list("id", flat=True)

        settled = 0
        for lot_id in due:
            settle_lot(lot_id, now)
            settled += 1

        self.stdout.write(self.style.SUCCESS(f"{settled} lote(s) liquidado(s)."))

        # Repõe no Redis as âncoras que ficaram para trás (o Redis estava fora do ar num lance).
        restored = sum(restore_anchor(lot) for lot in Lot.objects.filter(bid_count__gt=0))
        self.stdout.write(self.style.SUCCESS(f"{restored} âncora(s) reposta(s)."))
