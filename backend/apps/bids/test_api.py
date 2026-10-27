"""Testes da rota do lance: acesso, respostas e formato."""

from uuid import uuid4

import pytest
from django.urls import reverse

from apps.wallet.services import deposit


def bid_url(lot_id):
    return reverse("lot-bids", args=[lot_id])


@pytest.fixture
def live_lot(make_lot, bidder):
    deposit(bidder, 100_000)
    return make_lot()


@pytest.mark.parametrize("user_fixture", [None, "auctioneer"])
def test_only_bidders_can_bid(api_client, request, live_lot, user_fixture):
    if user_fixture:
        api_client.force_login(request.getfixturevalue(user_fixture))

    response = api_client.post(bid_url(live_lot.id), {"amount": 10_000}, format="json")

    assert response.status_code == 403


def test_bid_on_an_unknown_lot_answers_404(api_client, bidder):
    api_client.force_login(bidder)

    response = api_client.post(bid_url(uuid4()), {"amount": 10_000}, format="json")

    assert response.status_code == 404


def test_accepted_bid_returns_the_bid_and_the_updated_lot(api_client, bidder, live_lot):
    api_client.force_login(bidder)

    response = api_client.post(bid_url(live_lot.id), {"amount": 10_000}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["bid"]["sequence"] == 1
    assert body["bid"]["bidder_alias"] == bidder.public_alias
    assert body["lot"]["current_price"] == 10_000
    assert body["lot"]["minimum_next_bid"] == 10_500
    assert body["lot"]["leader_alias"] == bidder.public_alias
    assert body["extended"] is False
    assert bidder.email not in response.content.decode()


def test_rejected_bid_answers_422_with_the_code(api_client, bidder, live_lot):
    api_client.force_login(bidder)

    response = api_client.post(bid_url(live_lot.id), {"amount": 9_999}, format="json")

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "BELOW_MINIMUM"
    assert body["data"] == {"minimum": 10_000}
    assert "R$ 100,00" in body["message"]


@pytest.mark.parametrize("amount", [0, "cem reais"])
def test_amount_must_be_a_positive_number(api_client, bidder, live_lot, amount):
    api_client.force_login(bidder)

    response = api_client.post(bid_url(live_lot.id), {"amount": amount}, format="json")

    assert response.status_code == 400
    assert "amount" in response.json()
