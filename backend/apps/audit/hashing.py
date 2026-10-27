"""O hash de cada lance: o elo da cadeia que a auditoria recalcula."""

import hashlib
from datetime import UTC, datetime
from uuid import UUID

SEPARATOR = "|"


def format_timestamp(moment: datetime) -> str:
    """Um instante em UTC, com microssegundos: "2026-10-25T14:03:07.123456Z"."""
    if moment.tzinfo is None:
        raise ValueError("O horário do lance precisa ter fuso horário.")
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def bid_payload(
    *,
    lot_id: UUID | str,
    sequence: int,
    bidder_alias: str,
    amount: int,
    created_at: datetime,
    prev_hash: str,
) -> str:
    """O texto do lance no formato fixo da especificação."""
    parts = [
        str(lot_id),
        str(sequence),
        bidder_alias,
        str(amount),
        format_timestamp(created_at),
        prev_hash,
    ]
    return SEPARATOR.join(parts)


def compute_bid_hash(**fields) -> str:
    """SHA-256, em hexadecimal, do texto do lance. Recebe os mesmos campos do bid_payload."""
    return hashlib.sha256(bid_payload(**fields).encode("utf-8")).hexdigest()


def hash_of(bid) -> str:
    """Recalcula o hash de um lance a partir dos próprios campos dele."""
    return compute_bid_hash(
        lot_id=bid.lot_id,
        sequence=bid.sequence,
        bidder_alias=bid.bidder.public_alias,
        amount=bid.amount,
        created_at=bid.created_at,
        prev_hash=bid.prev_hash,
    )
