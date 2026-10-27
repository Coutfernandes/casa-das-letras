"""Testes da carteira: saldo calculado, depósito simulado e acesso."""

import pytest
from django.urls import reverse

from apps.auctions.models import Lot

from .models import WalletEntry
from .services import MAX_DEPOSIT, get_balance


def lead(lot, bidder, amount):
    """Coloca o licitante na liderança do lote, como se tivesse dado o lance."""
    Lot.objects.filter(id=lot.id).update(leader=bidder, current_price=amount, bid_count=1)


def give_money(bidder, amount):
    WalletEntry.objects.create(user=bidder, kind=WalletEntry.Kind.DEPOSIT, amount=amount)


@pytest.mark.parametrize("user_fixture", [None, "auctioneer"])
def test_wallet_is_only_for_bidders(api_client, request, user_fixture, db):
    if user_fixture:
        api_client.force_login(request.getfixturevalue(user_fixture))

    assert api_client.get(reverse("wallet")).status_code == 403
    assert api_client.post(reverse("wallet-deposit"), {"amount": 100}).status_code == 403


def test_new_wallet_starts_empty(api_client, bidder):
    api_client.force_login(bidder)

    body = api_client.get(reverse("wallet")).json()

    assert (body["total"], body["committed"], body["available"]) == (0, 0, 0)
    assert body["entries"] == []


def test_deposit_adds_to_total_and_available(api_client, bidder):
    api_client.force_login(bidder)

    response = api_client.post(reverse("wallet-deposit"), {"amount": 500_000}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 500_000
    assert body["available"] == 500_000
    assert [entry["kind"] for entry in body["entries"]] == ["DEPOSIT"]


@pytest.mark.parametrize("amount", [0, -100, MAX_DEPOSIT + 1])
def test_deposit_must_be_within_limits(api_client, bidder, amount):
    api_client.force_login(bidder)

    response = api_client.post(reverse("wallet-deposit"), {"amount": amount}, format="json")

    assert response.status_code == 400
    assert "amount" in response.json()
    assert not WalletEntry.objects.exists()


def test_leading_a_lot_commits_the_bid(bidder, make_lot):
    give_money(bidder, 500_000)
    lead(make_lot("live"), bidder, 120_000)

    balance = get_balance(bidder)

    assert (balance.total, balance.committed, balance.available) == (500_000, 120_000, 380_000)


def test_lot_past_its_end_still_commits_until_settled(bidder, make_lot):
    give_money(bidder, 500_000)
    lead(make_lot("finished"), bidder, 120_000)

    assert get_balance(bidder).committed == 120_000


@pytest.mark.parametrize("final_status", [Lot.Status.CLOSED, Lot.Status.CANCELLED])
def test_settled_or_cancelled_lots_free_the_bid(bidder, make_lot, final_status):
    give_money(bidder, 500_000)
    lot = make_lot("live")
    lead(lot, bidder, 120_000)
    Lot.objects.filter(id=lot.id).update(status=final_status)

    assert get_balance(bidder).available == 500_000


def test_being_outbid_frees_the_bid(bidder, make_lot):
    other = type(bidder).objects.create_user(
        email="outro.licitante@exemplo.com", password="SenhaSegura123!",
        name="Outra Pessoa", role=bidder.role,
    )
    give_money(bidder, 500_000)
    lot = make_lot("live")
    lead(lot, bidder, 120_000)

    lead(lot, other, 125_000)

    assert get_balance(bidder).available == 500_000


def test_wallet_shows_the_lots_that_commit_the_balance(api_client, bidder, make_lot):
    give_money(bidder, 500_000)
    lead(make_lot("live", title="O Guarani"), bidder, 115_000)
    api_client.force_login(bidder)

    body = api_client.get(reverse("wallet")).json()

    assert [lot["title"] for lot in body["committed_lots"]] == ["O Guarani"]
    assert body["committed"] == 115_000
