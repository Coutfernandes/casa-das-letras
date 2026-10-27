"""Testes de "meus arremates": lotes em disputa, lotes vencidos e a liquidação na hora."""

from datetime import timedelta

import pytest
from django.urls import reverse

from apps.auctions.models import Lot
from apps.auctions.settlement import settle_lot
from apps.wallet.services import deposit

from .services import place_bid

MY_BIDS_URL = reverse("my-bids")


@pytest.fixture
def contested_lot(make_lot, bidder, other_bidder):
    """Lote ao vivo: o licitante deu R$ 100 e R$ 130; o outro, R$ 120 no meio."""
    deposit(bidder, 100_000)
    deposit(other_bidder, 100_000)
    lot = make_lot()
    place_bid(lot.id, bidder, 10_000)
    place_bid(lot.id, other_bidder, 12_000)
    place_bid(lot.id, bidder, 13_000)
    return lot


def my_bids(api_client, user):
    api_client.force_login(user)
    response = api_client.get(MY_BIDS_URL)
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize("user_fixture", [None, "auctioneer"])
def test_only_bidders_see_their_bids(api_client, request, user_fixture):
    if user_fixture:
        api_client.force_login(request.getfixturevalue(user_fixture))

    response = api_client.get(MY_BIDS_URL)

    assert response.status_code == 403


def test_leader_sees_the_highest_of_their_bids_and_is_winning(api_client, contested_lot, bidder):
    body = my_bids(api_client, bidder)

    assert body["counts"] == {"bids": 1, "won": 0}
    [item] = body["bids"]
    assert item["lot"]["id"] == str(contested_lot.id)
    assert item["lot"]["phase"] == Lot.Phase.LIVE
    assert item["my_max_bid"] == 13_000
    assert item["winning"] is True


def test_outbid_bidder_sees_their_own_max_and_is_not_winning(
    api_client, contested_lot, other_bidder
):
    [item] = my_bids(api_client, other_bidder)["bids"]

    assert item["my_max_bid"] == 12_000
    assert item["winning"] is False


def test_open_lots_come_ordered_by_end(api_client, make_lot, bidder):
    deposit(bidder, 100_000)
    later = make_lot()
    sooner = make_lot()
    Lot.objects.filter(id=sooner.id).update(ends_at=later.ends_at - timedelta(minutes=30))
    place_bid(later.id, bidder, 10_000)
    place_bid(sooner.id, bidder, 10_000)

    ids = [item["lot"]["id"] for item in my_bids(api_client, bidder)["bids"]]

    assert ids == [str(sooner.id), str(later.id)]


def test_winner_sees_the_won_lot_with_its_receipt(api_client, ended_lot, other_bidder):
    lot = settle_lot(ended_lot.id)

    body = my_bids(api_client, other_bidder)

    assert body["counts"] == {"bids": 0, "won": 1}
    [item] = body["won"]
    assert item["lot"]["id"] == str(lot.id)
    assert item["lot"]["phase"] == Lot.Phase.CLOSED
    assert item["final_price"] == 12_000
    assert item["bid_count"] == 2
    assert item["closed_at"] is not None
    assert item["receipt_token"] == lot.receipt.public_token


def test_lot_won_by_someone_else_does_not_show_up(api_client, ended_lot, bidder):
    settle_lot(ended_lot.id)

    body = my_bids(api_client, bidder)

    assert body == {"bids": [], "won": [], "counts": {"bids": 0, "won": 0}}


def test_ended_lot_is_settled_on_the_spot_and_moves_to_won(
    api_client, contested_lot, end_now, bidder
):
    assert my_bids(api_client, bidder)["counts"] == {"bids": 1, "won": 0}

    end_now(contested_lot)
    body = my_bids(api_client, bidder)

    assert body["counts"] == {"bids": 0, "won": 1}
    assert body["won"][0]["lot"]["id"] == str(contested_lot.id)
    assert body["won"][0]["final_price"] == 13_000
    contested_lot.refresh_from_db()
    assert contested_lot.status == Lot.Status.CLOSED


def test_lot_detail_settles_an_ended_lot(api_client, ended_lot, other_bidder):
    response = api_client.get(reverse("lot-detail", args=[ended_lot.id]))

    assert response.status_code == 200
    body = response.json()
    assert body["phase"] == Lot.Phase.CLOSED
    assert body["winner_alias"] == other_bidder.public_alias
    assert body["final_price"] == 12_000
    ended_lot.refresh_from_db()
    assert ended_lot.status == Lot.Status.CLOSED
