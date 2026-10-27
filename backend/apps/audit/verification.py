"""
A verificação pública de um lote (seção 7 da especificação).

As 7 verificações rodam sempre, cada uma por conta própria: uma falha numa
não impede as outras de mostrar o que viram. O motivo (reason) é o código da
primeira que falhou, na ordem da especificação.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime

from django.db import transaction

from apps.auctions.models import Lot
from apps.bids.models import GENESIS_HASH

from .anchors import get_client, last_anchor
from .hashing import hash_of
from .models import Receipt
from .signing import verify_anchor

INTACT = "INTEGRO"
TAMPERED = "ADULTERADO"

OK = "ok"
FAIL = "fail"
WARN = "warn"
SKIPPED = "skipped"

WARNING_MESSAGES = {
    "external_copy_behind": "Cópia externa atrasada.",
    "external_copy_unavailable": "Cópia externa indisponível.",
}


@dataclass
class Check:
    key: str
    label: str
    status: str
    note: str
    # Código da falha ou do aviso. Não vai para a resposta: aparece em reason ou em warnings.
    code: str | None = None
    # Lances com problema nesta verificação.
    broken: list[int] = field(default_factory=list)


@dataclass
class BidRow:
    sequence: int
    bidder_alias: str
    amount: int
    created_at: datetime
    prev_hash: str
    hash: str
    ok: bool


@dataclass
class VerificationResult:
    status: str
    reason: str | None
    first_broken_sequence: int | None
    warnings: list[dict]
    checks: list[Check]
    bids: list[BidRow]

    def as_dict(self) -> dict:
        """O resultado pronto para a API, sem os campos internos das verificações."""
        return {
            "status": self.status,
            "reason": self.reason,
            "first_broken_sequence": self.first_broken_sequence,
            "warnings": self.warnings,
            "checks": [
                {"key": c.key, "label": c.label, "status": c.status, "note": c.note}
                for c in self.checks
            ],
            "bids": [asdict(bid) for bid in self.bids],
        }


def verify_lot(lot: Lot) -> VerificationResult:
    """Confere a cadeia de lances, a âncora assinada, a cópia no Redis e o comprovante do lote."""
    # O Redis vem antes do banco. As cópias só são feitas depois que o lance é gravado,
    # então, lido antes, o Redis nunca parece estar à frente do banco sem ter havido retrocesso.
    external = last_anchor(lot.id)
    external_on = get_client() is not None

    with transaction.atomic():
        # Trava o lote enquanto lê: um lance novo espera, e lote e lances ficam do mesmo instante.
        lot.refresh_from_db(from_queryset=Lot.objects.select_for_update())
        bids = list(lot.bids.select_related("bidder").order_by("sequence"))
        receipt = Receipt.objects.filter(lot=lot).first()

    checks = [
        check_sequence(bids),
        check_hashes(bids),
        check_chain(bids),
        check_anchor(lot, bids),
        check_signature(lot),
        check_external_copy(lot, external, external_on),
        check_receipt(lot, receipt),
    ]

    failed = [c for c in checks if c.status == FAIL]
    broken = {sequence for c in checks for sequence in c.broken}
    return VerificationResult(
        status=TAMPERED if failed else INTACT,
        reason=failed[0].code if failed else None,
        first_broken_sequence=min(broken) if broken else None,
        warnings=[
            {"code": c.code, "message": WARNING_MESSAGES[c.code]} for c in checks if c.status == WARN
        ],
        checks=checks,
        bids=[
            BidRow(
                sequence=bid.sequence,
                bidder_alias=bid.bidder.public_alias,
                amount=bid.amount,
                created_at=bid.created_at,
                prev_hash=bid.prev_hash,
                hash=bid.hash,
                ok=bid.sequence not in broken,
            )
            for bid in bids
        ],
    )


def check_sequence(bids) -> Check:
    """Os números dos lances são 1, 2, ..., n, sem lacunas nem repetições."""
    label = "Sequência contínua"
    broken = []
    note = ""
    previous = 0
    for bid in bids:
        # Cada lance tem o número do anterior mais 1. O primeiro, o número 1.
        if bid.sequence != previous + 1:
            if not broken:
                where = f"depois do lance #{previous}" if previous else "no início"
                note = f"Lacuna {where}: o próximo é o #{bid.sequence}."
            broken.append(bid.sequence)
        previous = bid.sequence
    if broken:
        return Check("sequence", label, FAIL, note, "sequence_gap", broken)
    if not bids:
        return Check("sequence", label, OK, "Nenhum lance registrado.")
    return Check("sequence", label, OK, f"Lances de #1 a #{len(bids)}, sem lacunas.")


def check_hashes(bids) -> Check:
    """Cada hash gravado é o SHA-256 dos próprios campos do lance."""
    label = "Hashes recalculados"
    broken = [bid.sequence for bid in bids if hash_of(bid) != bid.hash]
    if broken:
        note = f"Lance #{broken[0]}: os dados gravados não geram o hash gravado."
        return Check("hashes", label, FAIL, note, "hash_mismatch", broken)
    if not bids:
        return Check("hashes", label, OK, "Nenhum lance para recalcular.")
    return Check("hashes", label, OK, f"{len(bids)} hash(es) recalculado(s), todos iguais aos gravados.")


def check_chain(bids) -> Check:
    """Cada lance aponta para o hash gravado do anterior (o primeiro, para GENESIS)."""
    label = "Encadeamento"
    broken = []
    expected_prev = GENESIS_HASH
    for bid in bids:
        if bid.prev_hash != expected_prev:
            broken.append(bid.sequence)
        expected_prev = bid.hash
    if broken:
        note = f"Lance #{broken[0]}: não aponta para o hash do lance anterior."
        return Check("chain", label, FAIL, note, "chain_broken", broken)
    if not bids:
        return Check("chain", label, OK, "Nenhum lance para encadear.")
    return Check("chain", label, OK, "Cada lance aponta para o hash do anterior.")


def check_anchor(lot, bids) -> Check:
    """O número de lances e o último hash batem com a âncora gravada no lote."""
    label = "Âncora do lote"
    last_hash = bids[-1].hash if bids else ""
    if len(bids) != lot.bid_count:
        note = f"O lote registra {lot.bid_count} lance(s), mas há {len(bids)} no banco."
        return Check("anchor", label, FAIL, note, "anchor_mismatch")
    if last_hash != lot.last_bid_hash:
        return Check("anchor", label, FAIL, "O último hash não é o registrado no lote.", "anchor_mismatch")
    if not bids:
        return Check("anchor", label, OK, "Lote sem lances e sem âncora.")
    return Check("anchor", label, OK, f"{len(bids)} lance(s) e último hash iguais aos do lote.")


def check_signature(lot) -> Check:
    """A âncora do lote foi assinada pela chave privada do servidor."""
    label = "Assinatura Ed25519"
    if lot.bid_count == 0 and not lot.last_bid_hash and not lot.anchor_signature:
        return Check("signature", label, OK, "Lote sem lances: não há o que assinar.")
    if not verify_anchor(lot.id, lot.bid_count, lot.last_bid_hash, lot.anchor_signature):
        note = "A assinatura não confere com a chave pública do servidor."
        return Check("signature", label, FAIL, note, "bad_signature")
    return Check("signature", label, OK, "Âncora assinada pela chave do servidor.")


def check_external_copy(lot, external: dict | None, external_on: bool) -> Check:
    """Compara a âncora do lote com a última cópia no Redis, que só recebe inserções."""
    label = "Cópia externa da âncora"
    if external is None:
        if lot.bid_count == 0 and external_on:
            return Check("external_copy", label, OK, "Lote sem lances: nada a copiar.")
        note = "Não foi possível consultar a cópia externa."
        return Check("external_copy", label, WARN, note, "external_copy_unavailable")

    copied_count = int(external.get("bid_count", 0))
    copied_hash = external.get("last_bid_hash", "")
    if copied_count > lot.bid_count:
        note = f"A cópia externa registra {copied_count} lance(s); o lote, só {lot.bid_count}."
        return Check("external_copy", label, FAIL, note, "anchor_rollback")
    if copied_count == lot.bid_count and copied_hash != lot.last_bid_hash:
        note = "Mesmo número de lances, mas o último hash é outro."
        return Check("external_copy", label, FAIL, note, "anchor_rollback")
    if copied_count < lot.bid_count:
        note = f"A cópia externa vai até o lance #{copied_count}; o lote, até o #{lot.bid_count}."
        return Check("external_copy", label, WARN, note, "external_copy_behind")
    note = f"Cópia externa igual: {copied_count} lance(s), mesmo último hash."
    return Check("external_copy", label, OK, note)


def check_receipt(lot, receipt: Receipt | None) -> Check:
    """O comprovante do lote encerrado repete o valor final e o último hash do lote."""
    label = "Comprovante"
    if lot.status != Lot.Status.CLOSED or receipt is None:
        return Check("receipt", label, SKIPPED, "O lote ainda não tem comprovante.")
    if receipt.last_bid_hash != lot.last_bid_hash or receipt.amount != lot.final_price:
        note = "O valor ou o último hash do comprovante não é o do lote."
        return Check("receipt", label, FAIL, note, "receipt_mismatch")
    return Check("receipt", label, OK, "Valor e último hash iguais aos do lote.")
