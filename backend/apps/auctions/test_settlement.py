"""Testes da liquidação: quem vence paga, o leiloeiro recebe, e nada acontece duas vezes."""

import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.audit.models import Receipt
from apps.bids.services import place_bid
from apps.wallet.models import WalletEntry
from apps.wallet.services import get_balance
from core.exceptions import BusinessRuleError

from .models import Lot
from .settlement import settle_lot


def test_winner_pays_and_auctioneer_receives(ended_lot, auctioneer, other_bidder):
    lot = settle_lot(ended_lot.id)

    assert lot.status == Lot.Status.CLOSED
    assert (lot.winner_id, lot.final_price) == (other_bidder.id, 12_000)
    assert lot.closed_at is not None
    entries = set(WalletEntry.objects.filter(lot=lot).values_list("user_id", "kind", "amount"))
    assert entries == {
        (other_bidder.id, WalletEntry.Kind.SETTLEMENT_DEBIT, -12_000),
        (auctioneer.id, WalletEntry.Kind.SETTLEMENT_CREDIT, 12_000),
    }


def test_paying_moves_the_money_from_committed_to_spent(ended_lot, bidder, other_bidder):
    settle_lot(ended_lot.id)

    winner = get_balance(other_bidder)
    assert (winner.total, winner.committed, winner.available) == (88_000, 0, 88_000)
    assert get_balance(bidder).available == 100_000


def test_receipt_links_the_winner_alias_to_the_last_bid(ended_lot, other_bidder):
    lot = settle_lot(ended_lot.id)

    receipt = Receipt.objects.get(lot=lot)
    assert receipt.winner_alias == other_bidder.public_alias
    assert receipt.amount == 12_000
    assert receipt.last_bid_hash == lot.last_bid_hash
    assert len(receipt.public_token) >= 32


def test_lot_without_bids_closes_without_a_winner(make_lot):
    lot = settle_lot(make_lot("finished").id)

    assert lot.status == Lot.Status.CLOSED
    assert lot.winner_id is None
    assert not WalletEntry.objects.filter(lot=lot).exists()
    assert not Receipt.objects.filter(lot=lot).exists()


def test_settling_twice_changes_nothing(ended_lot):
    settle_lot(ended_lot.id)
    settle_lot(ended_lot.id)

    assert Receipt.objects.filter(lot=ended_lot).count() == 1
    assert WalletEntry.objects.filter(lot=ended_lot).count() == 2


def test_lot_still_running_is_not_settled(make_lot):
    lot = settle_lot(make_lot("live").id)

    assert lot.status == Lot.Status.OPEN


def test_cancelled_lot_stays_cancelled(make_lot):
    lot = make_lot("finished")
    Lot.objects.filter(id=lot.id).update(status=Lot.Status.CANCELLED)

    assert settle_lot(lot.id).status == Lot.Status.CANCELLED


def test_bid_after_the_end_settles_the_lot_and_is_refused(ended_lot, bidder, other_bidder):
    with pytest.raises(BusinessRuleError) as info:
        place_bid(ended_lot.id, bidder, 20_000)

    assert info.value.code == "LOT_CLOSED"
    ended_lot.refresh_from_db()
    assert ended_lot.status == Lot.Status.CLOSED
    assert ended_lot.winner_id == other_bidder.id


def test_close_due_lots_settles_only_what_has_ended(ended_lot, make_lot):
    running = make_lot("live")

    call_command("close_due_lots")

    ended_lot.refresh_from_db()
    running.refresh_from_db()
    assert ended_lot.status == Lot.Status.CLOSED
    assert running.status == Lot.Status.OPEN


def test_dashboard_shows_the_money_received(api_client, ended_lot, auctioneer):
    settle_lot(ended_lot.id)
    api_client.force_login(auctioneer)

    summary = api_client.get(reverse("auctioneer-lots")).json()["summary"]

    assert summary["total_received"] == 12_000
