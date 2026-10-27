"""Testes do motor de lances: as regras, a cadeia de hashes e o anti-sniping."""

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied

from apps.auctions.models import Lot
from apps.audit.hashing import hash_of
from apps.wallet.services import deposit, get_balance
from core.exceptions import BusinessRuleError

from .models import GENESIS_HASH, Bid
from .services import ANTI_SNIPING_WINDOW, place_bid

BALANCE = 100_000  # R$ 1.000,00 para cada licitante


@pytest.fixture
def funded(bidder, other_bidder):
    """Os dois licitantes começam com R$ 1.000,00 na carteira."""
    deposit(bidder, BALANCE)
    deposit(other_bidder, BALANCE)


def rejection(lot, user, amount, **options):
    """Dá um lance que deve ser recusado e devolve o erro."""
    with pytest.raises(BusinessRuleError) as info:
        place_bid(lot.id, user, amount, **options)
    return info.value


# ---------------------------------------------------------------------------
# Lances aceitos e a cadeia de hashes
# ---------------------------------------------------------------------------


def test_first_bid_at_the_starting_price_takes_the_lead(make_lot, bidder, funded):
    lot = make_lot()

    bid = place_bid(lot.id, bidder, 10_000).bid

    lot.refresh_from_db()
    assert (lot.leader, lot.current_price, lot.bid_count) == (bidder, 10_000, 1)
    assert (bid.sequence, bid.prev_hash) == (1, GENESIS_HASH)
    assert hash_of(Bid.objects.get(id=bid.id)) == bid.hash == lot.last_bid_hash


def test_each_bid_links_to_the_previous_one(make_lot, bidder, other_bidder, funded):
    lot = make_lot()

    first = place_bid(lot.id, bidder, 10_000).bid
    second = place_bid(lot.id, other_bidder, 10_500).bid

    assert second.sequence == 2
    assert second.prev_hash == first.hash


# ---------------------------------------------------------------------------
# As cinco recusas
# ---------------------------------------------------------------------------


def test_first_bid_below_the_starting_price_is_rejected(make_lot, bidder, funded):
    error = rejection(make_lot(), bidder, 9_999)

    assert error.code == "BELOW_MINIMUM"
    assert error.data == {"minimum": 10_000}
    assert "R$ 100,00" in error.message


def test_bid_below_current_plus_increment_is_rejected(make_lot, bidder, other_bidder, funded):
    lot = make_lot()
    place_bid(lot.id, bidder, 10_000)

    error = rejection(lot, other_bidder, 10_499)

    assert error.code == "BELOW_MINIMUM"
    assert error.data == {"minimum": 10_500}


def test_leader_cannot_cover_their_own_bid(make_lot, bidder, funded):
    lot = make_lot()
    place_bid(lot.id, bidder, 10_000)

    assert rejection(lot, bidder, 20_000).code == "ALREADY_WINNING"


@pytest.mark.parametrize(
    ("phase", "status", "code"),
    [
        ("scheduled", Lot.Status.OPEN, "LOT_NOT_STARTED"),
        ("finished", Lot.Status.OPEN, "LOT_CLOSED"),
        ("live", Lot.Status.CANCELLED, "LOT_CLOSED"),
    ],
)
def test_bids_only_while_the_lot_is_live(make_lot, bidder, funded, phase, status, code):
    lot = make_lot(phase)
    Lot.objects.filter(id=lot.id).update(status=status)

    assert rejection(lot, bidder, 10_000).code == code


def test_bid_above_the_available_balance_is_rejected(make_lot, bidder, funded):
    error = rejection(make_lot(), bidder, BALANCE + 1)

    assert error.code == "INSUFFICIENT_BALANCE"
    assert error.data == {"available": BALANCE}


def test_auctioneer_cannot_bid(make_lot, auctioneer):
    lot = make_lot()

    with pytest.raises(PermissionDenied):
        place_bid(lot.id, auctioneer, 10_000)


def test_rejected_bid_writes_nothing(make_lot, bidder, funded):
    lot = make_lot()

    rejection(lot, bidder, 1)

    lot.refresh_from_db()
    assert not Bid.objects.exists()
    assert (lot.bid_count, lot.leader, lot.current_price) == (0, None, None)


# ---------------------------------------------------------------------------
# O saldo comprometido
# ---------------------------------------------------------------------------


def test_leading_one_lot_reduces_what_is_left_for_others(make_lot, bidder, funded):
    first, second = make_lot(), make_lot()
    place_bid(first.id, bidder, 80_000)

    error = rejection(second, bidder, 30_000)

    assert error.code == "INSUFFICIENT_BALANCE"
    assert error.data == {"available": 20_000}


def test_being_outbid_frees_the_money_for_another_lot(
    make_lot, bidder, other_bidder, funded
):
    first, second = make_lot(), make_lot()
    place_bid(first.id, bidder, 80_000)
    place_bid(first.id, other_bidder, 85_000)

    place_bid(second.id, bidder, 90_000)

    assert get_balance(bidder).committed == 90_000


# ---------------------------------------------------------------------------
# O anti-sniping
# ---------------------------------------------------------------------------


def test_bid_in_the_last_two_minutes_extends_the_end(make_lot, bidder, funded):
    lot = make_lot()
    now = lot.ends_at - timedelta(minutes=1, seconds=50)

    result = place_bid(lot.id, bidder, 10_000, now=now)

    lot.refresh_from_db()
    assert result.extended is True
    assert lot.ends_at == now + ANTI_SNIPING_WINDOW
    assert lot.original_ends_at < lot.ends_at


def test_bid_with_more_time_left_keeps_the_end(make_lot, bidder, funded):
    lot = make_lot()
    original_end = lot.ends_at
    now = original_end - timedelta(minutes=3)

    result = place_bid(lot.id, bidder, 10_000, now=now)

    lot.refresh_from_db()
    assert result.extended is False
    assert lot.ends_at == original_end
