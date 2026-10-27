"""Testes do hash dos lances: o formato fixo e o efeito de cada campo."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from apps.accounts.models import User
from apps.bids.models import GENESIS_HASH, Bid

from .hashing import bid_payload, compute_bid_hash, format_timestamp, hash_of

LOT_ID = "3f2c8a1e-5b7d-4c9a-8e6f-1a2b3c4d5e6f"
CREATED_AT = datetime(2026, 10, 25, 14, 3, 7, 123456, tzinfo=UTC)

FIELDS = {
    "lot_id": LOT_ID,
    "sequence": 1,
    "bidder_alias": "Licitante #a3f9c1",
    "amount": 125_000,
    "created_at": CREATED_AT,
    "prev_hash": GENESIS_HASH,
}

EXPECTED_PAYLOAD = (
    "3f2c8a1e-5b7d-4c9a-8e6f-1a2b3c4d5e6f|1|Licitante #a3f9c1|125000|"
    "2026-10-25T14:03:07.123456Z|GENESIS"
)
EXPECTED_HASH = "b9719324df00ac630bee4c12bf9228ff8625823dfde2dfefc23727a8535e9a8a"


def test_payload_follows_the_fixed_format():
    assert bid_payload(**FIELDS) == EXPECTED_PAYLOAD


def test_hash_is_the_sha256_of_the_payload():
    assert compute_bid_hash(**FIELDS) == EXPECTED_HASH


def test_the_same_bid_always_gets_the_same_hash():
    assert compute_bid_hash(**FIELDS) == compute_bid_hash(**FIELDS)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lot_id", "00000000-0000-0000-0000-000000000000"),
        ("sequence", 2),
        ("bidder_alias", "Licitante #000000"),
        ("amount", 125_001),
        ("created_at", CREATED_AT + timedelta(microseconds=1)),
        ("prev_hash", "0" * 64),
    ],
)
def test_changing_any_field_changes_the_hash(field, value):
    assert compute_bid_hash(**{**FIELDS, field: value}) != EXPECTED_HASH


def test_timestamp_is_always_written_in_utc():
    manaus = timezone(timedelta(hours=-4))
    same_moment_in_manaus = datetime(2026, 10, 25, 10, 3, 7, 123456, tzinfo=manaus)

    assert format_timestamp(same_moment_in_manaus) == "2026-10-25T14:03:07.123456Z"


def test_timestamp_without_time_zone_is_rejected():
    with pytest.raises(ValueError):
        format_timestamp(datetime(2026, 10, 25, 14, 3, 7))


def test_hash_of_a_bid_uses_its_own_fields():
    bid = Bid(
        lot_id=LOT_ID,
        bidder=User(public_alias="Licitante #a3f9c1"),
        sequence=1,
        amount=125_000,
        created_at=CREATED_AT,
        prev_hash=GENESIS_HASH,
    )

    assert hash_of(bid) == EXPECTED_HASH
