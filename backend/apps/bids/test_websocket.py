"""Testes do canal WebSocket da sala do lote."""

from uuid import uuid4

from datetime import datetime, timedelta

from channels.db import database_sync_to_async
from django.utils import timezone

from apps.auctions.models import Lot
from apps.auctions.services import cancel_lot
from core.exceptions import BusinessRuleError
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

async def join_room(lot_id):
    """Entra na sala do lote e descarta o snapshot, para ouvir só os próximos eventos."""
    room = WebsocketCommunicator(application, f"/ws/lots/{lot_id}/", headers=[FRONTEND_ORIGIN])
    connected, _ = await room.connect()
    assert connected
    await room.receive_json_from()
    return room


@pytest.mark.django_db(transaction=True)
def test_room_hears_each_accepted_bid(make_lot, bidder):
    lot = make_lot()
    deposit(bidder, 100_000)

    async def run():
        room = await join_room(lot.id)
        await database_sync_to_async(place_bid)(lot.id, bidder, 10_000)
        event = await room.receive_json_from(timeout=2)
        await room.disconnect()
        return event

    event = async_to_sync(run)()

    assert event["type"] == "bid.accepted"
    assert event["bid"]["amount"] == 10_000
    assert event["bid"]["bidder_alias"] == bidder.public_alias
    assert event["lot"]["minimum_next_bid"] == 10_500
    assert "server_now" in event


@pytest.mark.django_db(transaction=True)
def test_bid_near_the_end_also_announces_the_extension(make_lot, bidder):
    lot = make_lot()
    ending_soon = timezone.now() + timedelta(minutes=1)
    Lot.objects.filter(id=lot.id).update(ends_at=ending_soon)
    deposit(bidder, 100_000)

    async def run():
        room = await join_room(lot.id)
        await database_sync_to_async(place_bid)(lot.id, bidder, 10_000)
        events = [await room.receive_json_from(timeout=2) for _ in range(2)]
        await room.disconnect()
        return events

    events = async_to_sync(run)()

    assert [event["type"] for event in events] == ["bid.accepted", "lot.extended"]
    assert datetime.fromisoformat(events[1]["ends_at"]) > ending_soon


@pytest.mark.django_db(transaction=True)
def test_rejected_bid_announces_nothing(make_lot, bidder):
    lot = make_lot()
    deposit(bidder, 100_000)

    async def run():
        room = await join_room(lot.id)
        with pytest.raises(BusinessRuleError):
            await database_sync_to_async(place_bid)(lot.id, bidder, 1)
        heard_nothing = await room.receive_nothing(timeout=0.5)
        await room.disconnect()
        return heard_nothing

    assert async_to_sync(run)()


@pytest.mark.django_db(transaction=True)
def test_cancelling_the_lot_tells_the_room(make_lot, auctioneer):
    lot = make_lot()

    async def run():
        room = await join_room(lot.id)
        await database_sync_to_async(cancel_lot)(lot.id, auctioneer)
        event = await room.receive_json_from(timeout=2)
        await room.disconnect()
        return event

    event = async_to_sync(run)()

    assert event["type"] == "lot.cancelled"
    assert event["lot"]["phase"] == "CANCELLED"
