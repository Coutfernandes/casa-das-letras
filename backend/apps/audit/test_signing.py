"""Testes da assinatura Ed25519 da âncora dos lotes."""

import base64
from io import StringIO

import pytest
from cryptography.hazmat.primitives.serialization import load_der_public_key
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command

from apps.bids.services import place_bid
from apps.wallet.services import deposit

from .signing import anchor_payload, generate_key_text, public_key_text, sign_anchor, verify_anchor

LOT_ID = "3f2c8a1e-5b7d-4c9a-8e6f-1a2b3c4d5e6f"
LAST_HASH = "b9719324df00ac630bee4c12bf9228ff8625823dfde2dfefc23727a8535e9a8a"
ANCHOR = {"lot_id": LOT_ID, "bid_count": 3, "last_bid_hash": LAST_HASH}


def test_payload_follows_the_fixed_format():
    assert anchor_payload(**ANCHOR) == f"{LOT_ID}|3|{LAST_HASH}"


def test_signature_of_the_same_anchor_is_valid():
    signature = sign_anchor(**ANCHOR)

    assert verify_anchor(**ANCHOR, signature=signature) is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lot_id", "00000000-0000-0000-0000-000000000000"),
        ("bid_count", 4),
        ("last_bid_hash", "0" * 64),
    ],
)
def test_changing_any_part_of_the_anchor_invalidates_the_signature(field, value):
    signature = sign_anchor(**ANCHOR)

    assert verify_anchor(**{**ANCHOR, field: value}, signature=signature) is False


def test_signature_made_with_another_key_is_invalid(settings):
    signature = sign_anchor(**ANCHOR)
    settings.AUDIT_SIGNING_KEY = generate_key_text()

    assert verify_anchor(**ANCHOR, signature=signature) is False


@pytest.mark.parametrize(
    "signature",
    ["", "isto não é base64", base64.b64encode(b"curta demais").decode()],
)
def test_empty_or_unreadable_signature_is_invalid(signature):
    assert verify_anchor(**ANCHOR, signature=signature) is False


@pytest.mark.parametrize("key", ["", "não é base64", base64.b64encode(b"poucos bytes").decode()])
def test_signing_without_a_valid_key_is_a_configuration_error(settings, key):
    settings.AUDIT_SIGNING_KEY = key

    with pytest.raises(ImproperlyConfigured, match="generate_signing_key"):
        sign_anchor(**ANCHOR)


def test_public_key_is_shown_as_ed25519_der_in_base64():
    text = public_key_text()

    assert text.startswith("ed25519:")
    public_key = load_der_public_key(base64.b64decode(text.removeprefix("ed25519:")))
    signature = base64.b64decode(sign_anchor(**ANCHOR))
    public_key.verify(signature, anchor_payload(**ANCHOR).encode())  # levanta erro se não bater


def test_accepted_bid_signs_the_lot_anchor(make_lot, bidder):
    deposit(bidder, 100_000)
    lot = make_lot()

    place_bid(lot.id, bidder, 10_000)

    lot.refresh_from_db()
    assert lot.bid_count == 1
    assert verify_anchor(lot.id, lot.bid_count, lot.last_bid_hash, lot.anchor_signature) is True


def test_generate_signing_key_prints_a_usable_key(settings):
    output = StringIO()

    call_command("generate_signing_key", stdout=output)

    line = next(line for line in output.getvalue().splitlines() if line.startswith("AUDIT_SIGNING_KEY="))
    settings.AUDIT_SIGNING_KEY = line.removeprefix("AUDIT_SIGNING_KEY=")
    assert verify_anchor(**ANCHOR, signature=sign_anchor(**ANCHOR)) is True
