"""Testes do canal WebSocket da sala do lote."""

from uuid import uuid4

import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator

from apps.wallet.services import deposit
from core.asgi import application

from .services import place_bid

FRONTEND_ORIGIN = (b"origin", b"http://localhost:5173")


def open_room(path, origin=FRONTEND_ORIGIN):
    """Conecta na sala, lê a primeira mensagem e desconecta."""

    async def run():
        communicator = WebsocketCommunicator(application, path, headers=[origin])
        connected, _ = await communicator.connect()
        message = await communicator.receive_json_from() if connected else None
        await communicator.disconnect()
        return connected, message

    return async_to_sync(run)()


@pytest.mark.django_db(transaction=True)
def test_visitor_receives_the_room_snapshot_on_connect(make_lot):
    lot = make_lot()

    connected, message = open_room(f"/ws/lots/{lot.id}/")

    assert connected
    assert message["type"] == "lot.snapshot"
    assert message["lot"]["title"] == "Dom Casmurro"
    assert message["bids"] == []
    assert "server_now" in message


@pytest.mark.django_db(transaction=True)
def test_snapshot_brings_the_latest_bids_first(make_lot, bidder, other_bidder):
    lot = make_lot()
    deposit(bidder, 100_000)
    deposit(other_bidder, 100_000)
    place_bid(lot.id, bidder, 10_000)
    place_bid(lot.id, other_bidder, 10_500)

    _, message = open_room(f"/ws/lots/{lot.id}/")

    assert [bid["sequence"] for bid in message["bids"]] == [2, 1]
    assert message["lot"]["leader_alias"] == other_bidder.public_alias


@pytest.mark.django_db(transaction=True)
def test_unknown_lot_is_refused(db):
    connected, _ = open_room(f"/ws/lots/{uuid4()}/")

    assert not connected


@pytest.mark.django_db(transaction=True)
def test_connection_from_another_site_is_refused(make_lot):
    lot = make_lot()

    connected, _ = open_room(f"/ws/lots/{lot.id}/", origin=(b"origin", b"https://site-malicioso.com"))

    assert not connected
