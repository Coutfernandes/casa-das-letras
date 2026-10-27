"""
Cria os dados de demonstração (seção 13 da especificação): três contas, cinco lotes e os lances.

As datas são contadas a partir do momento em que o comando roda, e os livros vêm do
apps/seed/data/books.json, nunca da Open Library: o seed funciona sem internet.
"""

import json
from dataclasses import asdict, dataclass
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import Receipt
from apps.audit.signing import public_key_text
from apps.auctions.models import Lot
from apps.auctions.settlement import settle_lot
from apps.bids.models import Bid
from apps.bids.services import place_bid
from apps.catalog.models import CatalogItemSnapshot
from apps.catalog.open_library import CatalogBook
from apps.wallet.models import WalletEntry
from apps.wallet.services import deposit
from core.money import format_brl

BOOKS_FILE = Path(__file__).resolve().parents[2] / "data" / "books.json"

# Contas só de teste: a mesma senha nas três.
PASSWORD = "SenhaSegura123!"
DEPOSIT = 5_000_00
MIN_INCREMENT = 50_00

ACCOUNTS = {
    "auctioneer": ("leiloeiro@casadasletras.com", "Casa das Letras", User.Role.AUCTIONEER),
    "bidder1": ("licitante1@casadasletras.com", "Ana Souza", User.Role.BIDDER),
    "bidder2": ("licitante2@casadasletras.com", "Bruno Lima", User.Role.BIDDER),
}
SEED_EMAILS = [email for email, _, _ in ACCOUNTS.values()]

ALREADY_SEEDED = "O seed já existe. Use --reset para apagar e criar de novo."

# Descrição honesta: o catálogo devolve obras, não edições. Nada de "primeira edição" nem "autografado".
DESCRIPTION = "Exemplar de demonstração do catálogo. Estado de conservação ilustrativo."


@dataclass(frozen=True)
class SeedBid:
    bidder: str
    amount: int
    # Quando o lance foi dado, contado a partir de agora (negativo: no passado).
    at: timedelta


@dataclass(frozen=True)
class SeedLot:
    work_key: str
    starting_price: int
    starts_in: timedelta
    ends_in: timedelta
    description: str
    bids: tuple[SeedBid, ...] = ()
    settle: bool = False


LIVE_START = -timedelta(hours=1)
LIVE_END = timedelta(days=10)

LOTS = [
    SeedLot(
        work_key="/works/OL1003017W",
        starting_price=1_000_00,
        starts_in=-timedelta(days=3),
        ends_in=-timedelta(days=1),
        description=f"{DESCRIPTION} Lote já encerrado, com comprovante emitido.",
        bids=(
            SeedBid("bidder2", 1_000_00, -timedelta(days=2)),
            SeedBid("bidder1", 1_200_00, -timedelta(days=2) + timedelta(hours=1)),
        ),
        settle=True,
    ),
    SeedLot(
        work_key="/works/OL1003040W",
        starting_price=300_00,
        starts_in=LIVE_START,
        ends_in=LIVE_END,
        description=DESCRIPTION,
        bids=(
            SeedBid("bidder1", 300_00, -timedelta(minutes=50)),
            SeedBid("bidder2", 350_00, -timedelta(minutes=30)),
            SeedBid("bidder1", 400_00, -timedelta(minutes=10)),
        ),
    ),
    SeedLot(
        work_key="/works/OL1525639W",
        starting_price=250_00,
        starts_in=LIVE_START,
        ends_in=LIVE_END,
        description=DESCRIPTION,
        bids=(SeedBid("bidder2", 250_00, -timedelta(minutes=20)),),
    ),
    SeedLot(
        work_key="/works/OL10342454W",
        starting_price=200_00,
        starts_in=LIVE_START,
        ends_in=LIVE_END,
        description=DESCRIPTION,
    ),
    SeedLot(
        work_key="/works/OL1196681W",
        starting_price=500_00,
        starts_in=timedelta(days=1),
        ends_in=timedelta(days=8),
        description=f"{DESCRIPTION} Os lances abrem amanhã.",
    ),
]


def load_books() -> dict[str, CatalogBook]:
    """Os livros do JSON do repositório, pela chave da obra."""
    entries = json.loads(BOOKS_FILE.read_text(encoding="utf-8"))
    books = (
        CatalogBook(
            work_key=entry["work_key"],
            title=entry["title"],
            authors=entry["authors"],
            first_publish_year=entry["first_publish_year"],
            edition_count=entry["edition_count"],
            cover_id=entry["cover_i"],
        )
        for entry in entries
    )
    return {book.work_key: book for book in books}


def reset_data() -> None:
    """
    Apaga comprovantes, carteira, lances, lotes, livros e as contas do seed, nessa ordem
    (as chaves estrangeiras são PROTECT). QuerySet.delete() não passa pelo delete() do
    AppendOnlyModel, que bloqueia só a remoção de um objeto pelo código.
    """
    Receipt.objects.all().delete()
    WalletEntry.objects.all().delete()
    Bid.objects.all().delete()
    Lot.objects.all().delete()
    CatalogItemSnapshot.objects.all().delete()
    User.objects.filter(email__in=SEED_EMAILS).delete()


def create_accounts() -> dict[str, User]:
    users = {
        key: User.objects.create_user(email=email, password=PASSWORD, name=name, role=role)
        for key, (email, name, role) in ACCOUNTS.items()
    }
    for user in users.values():
        if user.is_bidder:
            deposit(user, DEPOSIT)
    return users


def create_lot(spec: SeedLot, book: CatalogBook, auctioneer: User, now) -> Lot:
    """
    Grava o livro e o lote como o create_lot, mas sem baixar a capa (usa o endereço da
    Open Library) e aceitando um período no passado, para o lote encerrado.
    """
    snapshot = CatalogItemSnapshot.objects.create(
        ol_work_key=book.work_key,
        title=book.title,
        authors=book.authors,
        first_publish_year=book.first_publish_year,
        edition_count=book.edition_count,
        cover_source_url=book.cover_url,
        raw=asdict(book),
    )
    return Lot.objects.create(
        auctioneer=auctioneer,
        item=snapshot,
        description=spec.description,
        starting_price=spec.starting_price,
        min_increment=MIN_INCREMENT,
        starts_at=now + spec.starts_in,
        ends_at=now + spec.ends_in,
    )


def create_lots(users: dict[str, User], now) -> list[Lot]:
    books = load_books()
    lots = []
    for spec in LOTS:
        lot = create_lot(spec, books[spec.work_key], users["auctioneer"], now)
        # Todo lance passa pelo place_bid: a cadeia de hashes e a assinatura nascem válidas.
        for bid in spec.bids:
            place_bid(lot.id, users[bid.bidder], bid.amount, now=now + bid.at)
        if spec.settle:
            # Liquidado no instante em que terminou: o comprovante diz "encerrado há 1 dia".
            settle_lot(lot.id, now=now + spec.ends_in)
        lot.refresh_from_db()
        lots.append(lot)
    return lots


class Command(BaseCommand):
    help = "Cria as contas, os lotes e os lances de demonstração. Com --reset, apaga e cria de novo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Apaga todos os lotes, lances, carteiras, comprovantes e livros, e as contas do seed.",
        )

    def handle(self, *args, **options):
        # Sem a chave, nenhum lance pode ser assinado: para antes de mexer no banco.
        try:
            public_key_text()
        except ImproperlyConfigured as error:
            raise CommandError(str(error)) from error

        now = timezone.now()
        # Tudo ou nada: se algo falhar no meio, o banco volta a como estava antes do comando.
        with transaction.atomic():
            if options["reset"]:
                reset_data()
            elif User.objects.filter(email__in=SEED_EMAILS).exists():
                self.stdout.write(self.style.WARNING(ALREADY_SEEDED))
                return
            users = create_accounts()
            lots = create_lots(users, now)

        self.print_summary(users, lots)

    def print_summary(self, users: dict[str, User], lots: list[Lot]) -> None:
        self.stdout.write(self.style.SUCCESS("Seed criado."))
        self.stdout.write(f"\nContas (senha de todas: {PASSWORD}):")
        for user in users.values():
            self.stdout.write(f"  {user.email:<32} {user.name:<16} {user.get_role_display()}")

        now = timezone.now()
        self.stdout.write("\nLotes:")
        for lot in lots:
            phase = Lot.Phase(lot.phase_at(now)).label
            price = format_brl(lot.current_price) if lot.current_price else "sem lances"
            self.stdout.write(f"  {lot.item.title:<34} {phase:<10} {price}")
