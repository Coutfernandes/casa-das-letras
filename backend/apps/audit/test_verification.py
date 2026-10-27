"""
Testes da verificação do lote: cada adulteração é pega pela verificação certa.

Para simular quem mexe direto no banco, os lances são alterados com SQL puro:
o AppendOnlyModel não deixa o Django alterar nem apagar um lance.
"""

import uuid
from datetime import timedelta
from io import StringIO

import pytest
import redis
from django.core.management import call_command
from django.db import connection

from apps.auctions.models import Lot
from apps.auctions.settlement import settle_lot
from apps.bids.models import Bid
from apps.bids.services import place_bid
from apps.wallet.services import deposit

from . import anchors
from .hashing import compute_bid_hash, hash_of
from .models import Receipt
from .signing import generate_key_text, sign_anchor
from .verification import verify_lot

BIDS = Bid._meta.db_table
RECEIPTS = Receipt._meta.db_table


class BrokenRedis:
    """Um cliente que se comporta como um Redis fora do ar."""

    def rpush(self, *args):
        raise redis.exceptions.ConnectionError("Redis fora do ar")

    def lindex(self, *args):
        raise redis.exceptions.ConnectionError("Redis fora do ar")


def run_sql(sql, params):
    """Executa SQL direto no banco, por fora do Django, como faria quem adultera."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params)


def delete_bid(lot, sequence):
    run_sql(f"DELETE FROM {BIDS} WHERE lot_id = %s AND sequence = %s", [lot.id, sequence])


def statuses(result):
    return {check.key: check.status for check in result.checks}


@pytest.fixture
def funded(bidder, other_bidder):
    deposit(bidder, 100_000)
    deposit(other_bidder, 100_000)


@pytest.fixture
def give_bid(funded, django_capture_on_commit_callbacks):
    """Dá um lance e roda o que ele agenda para depois do commit (a cópia no Redis)."""

    def _give(lot, user, amount):
        with django_capture_on_commit_callbacks(execute=True):
            return place_bid(lot.id, user, amount)

    return _give


@pytest.fixture
def three_bids(make_lot, bidder, other_bidder, give_bid):
    """Um lote ao vivo com 3 lances, todos copiados no Redis."""
    lot = make_lot()
    give_bid(lot, bidder, 10_000)
    give_bid(lot, other_bidder, 12_000)
    give_bid(lot, bidder, 13_000)
    return lot


def test_untouched_lot_is_intact(three_bids, bidder, other_bidder):
    result = verify_lot(three_bids)

    assert result.status == "INTEGRO"
    assert result.reason is None
    assert result.first_broken_sequence is None
    assert result.warnings == []
    assert statuses(result) == {
        "sequence": "ok",
        "hashes": "ok",
        "chain": "ok",
        "anchor": "ok",
        "signature": "ok",
        "external_copy": "ok",
        "receipt": "skipped",
    }
    assert [check.label for check in result.checks] == [
        "Sequência contínua",
        "Hashes recalculados",
        "Encadeamento",
        "Âncora do lote",
        "Assinatura Ed25519",
        "Cópia externa da âncora",
        "Comprovante",
    ]
    assert result.checks[0].note == "Lances de #1 a #3, sem lacunas."
    assert [(b.sequence, b.bidder_alias, b.amount, b.ok) for b in result.bids] == [
        (1, bidder.public_alias, 10_000, True),
        (2, other_bidder.public_alias, 12_000, True),
        (3, bidder.public_alias, 13_000, True),
    ]
    assert result.bids[0].prev_hash == "GENESIS"
    assert result.bids[1].prev_hash == result.bids[0].hash


def test_lot_without_bids_is_intact(make_lot):
    result = verify_lot(make_lot())

    assert result.status == "INTEGRO"
    assert result.reason is None
    assert result.warnings == []
    assert result.bids == []
    assert statuses(result)["signature"] == "ok"
    assert statuses(result)["receipt"] == "skipped"


def test_changed_amount_is_a_hash_mismatch(three_bids):
    run_sql(f"UPDATE {BIDS} SET amount = 99000 WHERE lot_id = %s AND sequence = 2", [three_bids.id])

    result = verify_lot(three_bids)

    assert result.status == "ADULTERADO"
    assert result.reason == "hash_mismatch"
    assert result.first_broken_sequence == 2
    assert [bid.ok for bid in result.bids] == [True, False, True]
    assert result.checks[1].note == "Lance #2: os dados gravados não geram o hash gravado."
    # Os hashes gravados continuam encadeados: só o recálculo denuncia a troca do valor.
    assert statuses(result)["chain"] == "ok"


def test_deleted_middle_bid_is_a_sequence_gap(three_bids):
    delete_bid(three_bids, 2)

    result = verify_lot(three_bids)

    assert result.status == "ADULTERADO"
    assert result.reason == "sequence_gap"
    assert result.first_broken_sequence == 3
    assert result.checks[0].note == "Lacuna depois do lance #1: o próximo é o #3."
    assert [bid.sequence for bid in result.bids] == [1, 3]


@pytest.mark.parametrize(
    ("fix_hashes", "reason"),
    [
        # Só renumerar: o número do lance entra no hash, então o recálculo já denuncia.
        (False, "hash_mismatch"),
        # Recalcular os hashes dos renumerados: o elo com o lance inserido continua quebrado.
        (True, "chain_broken"),
    ],
)
def test_inserted_bid_in_the_middle_is_caught(three_bids, other_bidder, fix_hashes, reason):
    first = Bid.objects.get(lot=three_bids, sequence=1)
    # Abre espaço para o lance falso (em dois passos, por causa da sequência única por lote).
    where = "WHERE lot_id = %s"
    run_sql(f"UPDATE {BIDS} SET sequence = sequence + 100 {where} AND sequence >= 2", [three_bids.id])
    run_sql(f"UPDATE {BIDS} SET sequence = sequence - 99 {where} AND sequence > 100", [three_bids.id])
    created_at = first.created_at + timedelta(seconds=1)
    forged_hash = compute_bid_hash(
        lot_id=three_bids.id,
        sequence=2,
        bidder_alias=other_bidder.public_alias,
        amount=11_000,
        created_at=created_at,
        prev_hash=first.hash,
    )
    run_sql(
        f"INSERT INTO {BIDS} (id, lot_id, bidder_id, sequence, amount, created_at, prev_hash, hash) "
        "VALUES (%s, %s, %s, 2, 11000, %s, %s, %s)",
        [uuid.uuid4(), three_bids.id, other_bidder.id, created_at, first.hash, forged_hash],
    )
    if fix_hashes:
        for bid in Bid.objects.filter(lot=three_bids, sequence__gte=3).select_related("bidder"):
            run_sql(f"UPDATE {BIDS} SET hash = %s WHERE id = %s", [hash_of(bid), bid.id])

    result = verify_lot(three_bids)

    assert result.status == "ADULTERADO"
    assert result.reason == reason
    assert result.first_broken_sequence == 3
    assert statuses(result)["sequence"] == "ok"
    assert statuses(result)["anchor"] == "fail"


def test_deleted_last_bid_is_an_anchor_mismatch(three_bids):
    delete_bid(three_bids, 3)

    result = verify_lot(three_bids)

    assert result.status == "ADULTERADO"
    assert result.reason == "anchor_mismatch"
    assert result.first_broken_sequence is None
    assert result.checks[3].note == "O lote registra 3 lance(s), mas há 2 no banco."
    assert statuses(result) == {
        "sequence": "ok",
        "hashes": "ok",
        "chain": "ok",
        "anchor": "fail",
        "signature": "ok",
        "external_copy": "ok",
        "receipt": "skipped",
    }


def test_anchor_signed_with_another_key_is_a_bad_signature(three_bids, settings):
    delete_bid(three_bids, 3)
    second = Bid.objects.get(lot=three_bids, sequence=2)
    # Quem adultera não tem a chave do servidor: assina a âncora nova com uma chave sua.
    server_key = settings.AUDIT_SIGNING_KEY
    settings.AUDIT_SIGNING_KEY = generate_key_text()
    forged_signature = sign_anchor(three_bids.id, 2, second.hash)
    settings.AUDIT_SIGNING_KEY = server_key
    Lot.objects.filter(id=three_bids.id).update(
        bid_count=2, last_bid_hash=second.hash, anchor_signature=forged_signature
    )

    result = verify_lot(three_bids)

    assert result.status == "ADULTERADO"
    assert result.reason == "bad_signature"
    assert statuses(result)["anchor"] == "ok"
    assert statuses(result)["signature"] == "fail"


def test_restored_old_anchor_is_a_rollback(make_lot, bidder, other_bidder, give_bid):
    lot = make_lot()
    give_bid(lot, bidder, 10_000)
    give_bid(lot, other_bidder, 12_000)
    lot.refresh_from_db()
    saved = {
        "bid_count": lot.bid_count,
        "last_bid_hash": lot.last_bid_hash,
        "anchor_signature": lot.anchor_signature,
    }
    give_bid(lot, bidder, 13_000)
    give_bid(lot, other_bidder, 14_000)
    # Some com os 2 últimos lances e volta o lote para a âncora antiga, que tem assinatura válida.
    delete_bid(lot, 4)
    delete_bid(lot, 3)
    Lot.objects.filter(id=lot.id).update(**saved)

    result = verify_lot(lot)

    assert result.status == "ADULTERADO"
    assert result.reason == "anchor_rollback"
    assert result.checks[5].note == "A cópia externa registra 4 lance(s); o lote, só 2."
    assert statuses(result) == {
        "sequence": "ok",
        "hashes": "ok",
        "chain": "ok",
        "anchor": "ok",
        "signature": "ok",
        "external_copy": "fail",
        "receipt": "skipped",
    }

    # Repor a âncora não pode apagar a prova: a cópia à frente do lote fica como está.
    call_command("close_due_lots", stdout=StringIO())
    assert verify_lot(lot).reason == "anchor_rollback"


def test_same_count_with_another_hash_is_a_rollback(three_bids, fake_redis):
    fake_redis.rpush(
        anchors.anchors_key(three_bids.id),
        '{"bid_count": 3, "last_bid_hash": "outro", "signature": ""}',
    )

    result = verify_lot(three_bids)

    assert result.reason == "anchor_rollback"


def test_external_copy_behind_is_a_warning_until_the_anchor_is_restored(
    make_lot, bidder, other_bidder, give_bid, monkeypatch, fake_redis, end_now
):
    lot = make_lot()
    give_bid(lot, bidder, 10_000)
    # O Redis cai bem na hora do 2º lance: o lance vale, a cópia fica para trás.
    monkeypatch.setattr(anchors, "_connect", lambda url: BrokenRedis())
    give_bid(lot, other_bidder, 12_000)
    monkeypatch.setattr(anchors, "_connect", lambda url: fake_redis)

    result = verify_lot(lot)

    assert result.status == "INTEGRO"
    assert result.reason is None
    assert result.warnings == [{"code": "external_copy_behind", "message": "Cópia externa atrasada."}]
    assert statuses(result)["external_copy"] == "warn"

    end_now(lot)
    output = StringIO()
    call_command("close_due_lots", stdout=output)

    assert "1 lote(s) liquidado(s)." in output.getvalue()
    assert "1 âncora(s) reposta(s)." in output.getvalue()
    assert anchors.last_anchor(lot.id)["bid_count"] == 2
    result = verify_lot(lot)
    assert result.status == "INTEGRO"
    assert result.warnings == []
    assert statuses(result)["external_copy"] == "ok"
    assert statuses(result)["receipt"] == "ok"


def test_redis_off_is_a_warning(three_bids, settings):
    settings.REDIS_URL = ""

    result = verify_lot(three_bids)

    assert result.status == "INTEGRO"
    assert result.warnings == [
        {"code": "external_copy_unavailable", "message": "Cópia externa indisponível."}
    ]


def test_empty_copy_of_a_lot_with_bids_is_a_warning(ended_lot):
    # O ended_lot dá os lances sem rodar o que vem depois do commit: nada foi copiado.
    result = verify_lot(ended_lot)

    assert result.status == "INTEGRO"
    assert [warning["code"] for warning in result.warnings] == ["external_copy_unavailable"]


def test_changed_receipt_is_a_receipt_mismatch(ended_lot):
    settle_lot(ended_lot.id)
    run_sql(f"UPDATE {RECEIPTS} SET amount = 1000 WHERE lot_id = %s", [ended_lot.id])

    result = verify_lot(ended_lot)

    assert result.status == "ADULTERADO"
    assert result.reason == "receipt_mismatch"
    assert statuses(result)["receipt"] == "fail"
