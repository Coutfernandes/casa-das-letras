"""Testes do comprovante público: abre sem login e só mostra o pseudônimo do vencedor."""

import pytest
from django.urls import reverse

from apps.auctions.settlement import settle_lot
from apps.bids.models import Bid

from .models import Receipt


def receipt_url(token):
    return reverse("receipt-detail", args=[token])


@pytest.fixture
def receipt(ended_lot):
    settle_lot(ended_lot.id)
    return Receipt.objects.select_related("lot").get(lot=ended_lot)


def test_receipt_opens_without_login(api_client, receipt, other_bidder, auctioneer):
    response = api_client.get(receipt_url(receipt.public_token))

    assert response.status_code == 200
    body = response.json()
    last_bid = Bid.objects.filter(lot=receipt.lot).order_by("-sequence").first()
    assert body["token"] == receipt.public_token
    assert body["lot_id"] == str(receipt.lot.id)
    assert body["title"] == "Dom Casmurro"
    assert body["authors"] == ["Machado de Assis"]
    assert body["first_publish_year"] == 1899
    assert body["winner_alias"] == other_bidder.public_alias
    assert body["amount"] == 12_000
    assert body["closed_at"] is not None
    assert body["bid_count"] == 2
    assert body["auctioneer_name"] == auctioneer.name
    assert body["issued_at"] is not None
    assert body["last_bid_hash"] == last_bid.hash


def test_receipt_never_reveals_who_the_winner_is(api_client, receipt, other_bidder):
    content = api_client.get(receipt_url(receipt.public_token)).content.decode()

    assert other_bidder.email not in content
    assert other_bidder.name not in content
    assert str(other_bidder.id) not in content


def test_unknown_token_answers_404(api_client, receipt):
    response = api_client.get(receipt_url("token-que-nao-existe"))

    assert response.status_code == 404
