"""Liquida os lotes que já passaram do fim e que ninguém acessou. Em produção, o cron chama a mesma lógica."""

from django.core.management.base import BaseCommand

from apps.auctions.maintenance import run_tick


class Command(BaseCommand):
    help = "Liquida os lotes que já terminaram e ainda estão abertos, e repõe as âncoras atrasadas."

    def handle(self, *args, **options):
        result = run_tick()
        self.stdout.write(self.style.SUCCESS(f"{result.settled} lote(s) liquidado(s)."))
        self.stdout.write(self.style.SUCCESS(f"{result.restored} âncora(s) reposta(s)."))
