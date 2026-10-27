"""Testes da cópia externa das âncoras no Redis e do comando sign_missing_anchors."""

from io import StringIO

import pytest
import redis
from django.core.management import call_command

from apps.auctions.models import Lot
from apps.bids.models import Bid
from apps.bids.services import place_bid
from apps.wallet.services import deposit

from . import anchors
from .anchors import all_anchors, anchors_key, last_anchor
from .signing import verify_anchor


class BrokenRedis:
    """Um cliente que se comporta como um Redis fora do ar."""

    def rpush(self, *args):
        raise redis.exceptions.ConnectionError("Redis fora do ar")

    def lrange(self, *args):
        raise redis.exceptions.ConnectionError("Redis fora do ar")

    def lindex(self, *args):
        raise redis.exceptions.ConnectionError("Redis fora do ar")


@pytest.fixture
def funded(bidder, other_bidder):
    deposit(bidder, 100_000)
    deposit(other_bidder, 100_000)


def test_each_bid_appends_one_anchor_to_the_list(
    make_lot, bidder, other_bidder, funded, fake_redis, django_capture_on_commit_callbacks
):
    lot = make_lot()

    with django_capture_on_commit_callbacks(execute=True):
        place_bid(lot.id, bidder, 10_000)
    with django_capture_on_commit_callbacks(execute=True):
        place_bid(lot.id, other_bidder, 12_000)

    lot.refresh_from_db()
    assert fake_redis.llen(anchors_key(lot.id)) == 2
    assert [entry["bid_count"] for entry in all_anchors(lot.id)] == [1, 2]
    last = last_anchor(lot.id)
    assert last["bid_count"] == lot.bid_count
    assert last["last_bid_hash"] == lot.last_bid_hash
    assert last["signature"] == lot.anchor_signature
    assert verify_anchor(lot.id, last["bid_count"], last["last_bid_hash"], last["signature"])


def test_lot_without_anchors_has_no_last_anchor(make_lot):
    assert last_anchor(make_lot().id) is None


def test_without_redis_url_the_copy_is_off_and_bids_still_work(
    settings, make_lot, bidder, funded, fake_redis, django_capture_on_commit_callbacks
):
    settings.REDIS_URL = ""
    lot = make_lot()

    with django_capture_on_commit_callbacks(execute=True):
        placed = place_bid(lot.id, bidder, 10_000)

    assert placed.bid.sequence == 1
    assert fake_redis.keys("anchors:*") == []
    assert last_anchor(lot.id) is None
    assert all_anchors(lot.id) == []


def test_redis_down_does_not_undo_the_bid(
    monkeypatch, make_lot, bidder, funded, django_capture_on_commit_callbacks
):
    monkeypatch.setattr(anchors, "_connect", lambda url: BrokenRedis())
    lot = make_lot()

    with django_capture_on_commit_callbacks(execute=True):
        place_bid(lot.id, bidder, 10_000)

    lot.refresh_from_db()
    assert Bid.objects.filter(lot=lot).count() == 1
    assert verify_anchor(lot.id, lot.bid_count, lot.last_bid_hash, lot.anchor_signature)
    assert last_anchor(lot.id) is None
    assert all_anchors(lot.id) == []


def _unsigned_lot(make_lot, bidder, other_bidder):
    """Um lote com dois lances, como os criados antes da assinatura existir."""
    lot = make_lot()
    place_bid(lot.id, bidder, 10_000)
    place_bid(lot.id, other_bidder, 12_000)
    Lot.objects.filter(id=lot.id).update(anchor_signature="")
    return lot


def test_sign_missing_anchors_signs_intact_lots_and_skips_broken_ones(
    make_lot, bidder, other_bidder, funded, fake_redis, django_capture_on_commit_callbacks
):
    intact = _unsigned_lot(make_lot, bidder, other_bidder)
    broken = _unsigned_lot(make_lot, bidder, other_bidder)
    # Alguém mexeu no valor de um lance direto no banco: o hash não bate mais.
    Bid.objects.filter(lot=broken, sequence=1).update(amount=99_999)
    output = StringIO()

    with django_capture_on_commit_callbacks(execute=True):
        call_command("sign_missing_anchors", stdout=output)

    intact.refresh_from_db()
    broken.refresh_from_db()
    assert verify_anchor(intact.id, intact.bid_count, intact.last_bid_hash, intact.anchor_signature)
    assert broken.anchor_signature == ""
    assert last_anchor(intact.id)["signature"] == intact.anchor_signature
    assert last_anchor(broken.id) is None
    assert str(broken.id) in output.getvalue()
    assert "1 lote(s) assinado(s), 1 pulado(s)." in output.getvalue()
