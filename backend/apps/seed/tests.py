"""Testes do comando seed_data."""

from io import StringIO

import pytest
import requests
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import User
from apps.audit.models import Receipt
from apps.audit.verification import FAIL, INTACT, WARN, verify_lot
from apps.auctions.models import Lot
from apps.bids.models import Bid
from apps.catalog.models import CatalogItemSnapshot
from apps.seed.management.commands import seed_data
from apps.seed.management.commands.seed_data import ALREADY_SEEDED, PASSWORD, SEED_EMAILS
from apps.wallet.services import get_balance

pytestmark = pytest.mark.django_db


@pytest.fixture
def run_seed(django_capture_on_commit_callbacks):
    """Roda o comando como no terminal e devolve o que ele imprimiu.

    Os on_commit (cópia da âncora no Redis, avisos da sala) rodam como num banco de verdade.
    """

    def _run(*args):
        out = StringIO()
        with django_capture_on_commit_callbacks(execute=True):
            call_command("seed_data", *args, stdout=out)
        return out.getvalue()

    return _run


def seed_user(number):
    return User.objects.get(email=f"licitante{number}@casadasletras.com")


def lot_titled(title):
    return Lot.objects.get(item__title=title)


def test_creates_accounts_lots_bids_and_receipt(run_seed):
    run_seed()

    assert User.objects.filter(email__in=SEED_EMAILS).count() == 3
    assert all(user.check_password(PASSWORD) for user in User.objects.filter(email__in=SEED_EMAILS))
    assert User.objects.get(email="leiloeiro@casadasletras.com").role == User.Role.AUCTIONEER

    phases = sorted(lot.phase_at() for lot in Lot.objects.all())
    assert phases == sorted(["CLOSED", "LIVE", "LIVE", "LIVE", "SCHEDULED"])

    # 2 no encerrado + 3 em Dom Casmurro + 1 em O Guarani.
    assert Bid.objects.count() == 6
    assert Receipt.objects.count() == 1


def test_lots_have_the_expected_leaders_and_prices(run_seed):
    run_seed()

    closed = lot_titled("Memórias Póstumas de Brás Cubas")
    assert closed.winner == seed_user(1)
    assert closed.final_price == 1_200_00
    assert closed.receipt.amount == 1_200_00
    assert closed.receipt.winner_alias == seed_user(1).public_alias

    dom_casmurro = lot_titled("Dom Casmurro")
    assert (dom_casmurro.leader, dom_casmurro.current_price, dom_casmurro.bid_count) == (seed_user(1), 400_00, 3)
    amounts = list(dom_casmurro.bids.order_by("sequence").values_list("amount", flat=True))
    assert amounts == [300_00, 350_00, 400_00]

    guarani = lot_titled("O Guarani")
    assert (guarani.leader, guarani.current_price) == (seed_user(2), 250_00)

    assert lot_titled("O Cortiço").bid_count == 0
    assert all(lot.min_increment == 50_00 for lot in Lot.objects.all())


def test_every_seed_lot_audits_intact(run_seed):
    run_seed()

    for lot in Lot.objects.all():
        result = verify_lot(lot)
        assert result.status == INTACT, lot
        assert not [check for check in result.checks if check.status in (FAIL, WARN)], lot


def test_balances(run_seed):
    run_seed()

    first = get_balance(seed_user(1))
    assert (first.total, first.committed) == (5_000_00 - 1_200_00, 400_00)

    second = get_balance(seed_user(2))
    assert (second.total, second.committed) == (5_000_00, 250_00)

    auctioneer = get_balance(User.objects.get(email="leiloeiro@casadasletras.com"))
    assert auctioneer.total == 1_200_00


def test_books_use_the_open_library_cover_address_and_honest_descriptions(run_seed):
    run_seed()

    for snapshot in CatalogItemSnapshot.objects.all():
        assert not snapshot.cover
        assert snapshot.cover_url.startswith("https://covers.openlibrary.org/b/id/")
    for lot in Lot.objects.all():
        text = lot.description.lower()
        assert "primeira edição" not in text
        assert "autografad" not in text


def test_running_twice_without_reset_does_not_duplicate(run_seed):
    run_seed()
    output = run_seed()

    assert ALREADY_SEEDED in output
    assert User.objects.filter(email__in=SEED_EMAILS).count() == 3
    assert Lot.objects.count() == 5
    assert Bid.objects.count() == 6


def test_reset_recreates_everything_and_keeps_other_accounts(run_seed, make_user, make_lot):
    other = make_user(email="pessoa.real@exemplo.com")
    other_lot = make_lot()
    run_seed()
    old_lot_ids = set(Lot.objects.values_list("id", flat=True))

    run_seed("--reset")

    new_lot_ids = set(Lot.objects.values_list("id", flat=True))
    assert len(new_lot_ids) == 5
    assert not new_lot_ids & old_lot_ids
    assert not Lot.objects.filter(id=other_lot.id).exists()
    assert User.objects.filter(id=other.id).exists()
    assert User.objects.filter(email__in=SEED_EMAILS).count() == 3
    assert Bid.objects.count() == 6
    assert Receipt.objects.count() == 1


def test_works_without_internet(run_seed, monkeypatch):
    def no_internet(*args, **kwargs):
        raise requests.ConnectionError("sem internet")

    monkeypatch.setattr(requests, "get", no_internet)
    monkeypatch.setattr(requests.Session, "request", no_internet)

    run_seed()

    assert Lot.objects.count() == 5


def test_missing_signing_key_stops_before_touching_the_database(run_seed, settings):
    settings.AUDIT_SIGNING_KEY = ""

    with pytest.raises(CommandError, match="AUDIT_SIGNING_KEY está vazia"):
        run_seed()

    assert not User.objects.filter(email__in=SEED_EMAILS).exists()


def test_failure_in_the_middle_leaves_nothing_behind(run_seed, monkeypatch):
    def broken_settle(*args, **kwargs):
        raise RuntimeError("falha no meio do seed")

    monkeypatch.setattr(seed_data, "settle_lot", broken_settle)

    with pytest.raises(RuntimeError):
        run_seed()

    assert not User.objects.filter(email__in=SEED_EMAILS).exists()
    assert Lot.objects.count() == 0
    assert Bid.objects.count() == 0
