"""Regras de negócio dos lotes: criar e cancelar."""

from dataclasses import asdict, dataclass
from datetime import datetime

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import CatalogItemSnapshot
from apps.catalog.open_library import CatalogBook, fetch_cover
from core.exceptions import BusinessRuleError

from .models import Lot


@dataclass(frozen=True)
class LotTerms:
    """Condições do lote definidas pelo leiloeiro. Valores em centavos."""

    starting_price: int
    min_increment: int
    starts_at: datetime
    ends_at: datetime
    description: str = ""


def create_lot(auctioneer, book: CatalogBook, terms: LotTerms, now: datetime | None = None) -> Lot:
    """Copia o livro da Open Library para o banco e cria o lote com essas condições."""
    now = now or timezone.now()
    if not auctioneer.is_auctioneer:
        raise BusinessRuleError("NOT_AUCTIONEER", "Apenas leiloeiros podem criar lotes.")
    _check_period(terms, now)

    # Download fora da transação: uma rede lenta não deixa o banco esperando.
    cover = fetch_cover(book)

    with transaction.atomic():
        snapshot = CatalogItemSnapshot(
            ol_work_key=book.work_key,
            title=book.title,
            authors=book.authors,
            first_publish_year=book.first_publish_year,
            edition_count=book.edition_count,
            cover_source_url=book.cover_url,
            raw=asdict(book),
        )
        if cover is not None:
            snapshot.cover.save(f"{book.cover_id}.jpg", ContentFile(cover), save=False)
        snapshot.save()

        return Lot.objects.create(
            auctioneer=auctioneer,
            item=snapshot,
            description=terms.description,
            starting_price=terms.starting_price,
            min_increment=terms.min_increment,
            starts_at=terms.starts_at,
            ends_at=terms.ends_at,
        )


def cancel_lot(lot_id, auctioneer, now: datetime | None = None) -> Lot:
    """
    Cancela um lote do próprio leiloeiro, se ainda não tiver lances.

    Lança Lot.DoesNotExist se o lote não existir ou for de outro leiloeiro.
    """
    now = now or timezone.now()
    with transaction.atomic():
        lot = Lot.objects.select_for_update().get(id=lot_id, auctioneer=auctioneer)

        if lot.phase_at(now) not in (Lot.Phase.SCHEDULED, Lot.Phase.LIVE):
            raise BusinessRuleError("LOT_ALREADY_FINISHED", "Este lote já foi encerrado ou cancelado.")
        if lot.bid_count > 0:
            raise BusinessRuleError(
                "LOT_HAS_BIDS",
                "Este lote já recebeu lances e não pode ser cancelado.",
                {"bid_count": lot.bid_count},
            )

        lot.status = Lot.Status.CANCELLED
        lot.save(update_fields=["status"])
        return lot


def _check_period(terms: LotTerms, now: datetime) -> None:
    if terms.ends_at <= terms.starts_at:
        raise BusinessRuleError("LOT_INVALID_PERIOD", "O fim do lote precisa ser depois do início.")
    if terms.ends_at <= now:
        raise BusinessRuleError("LOT_ENDS_IN_PAST", "O fim do lote precisa estar no futuro.")
