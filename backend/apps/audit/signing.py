"""A assinatura Ed25519 da âncora de cada lote (seção 7 da especificação)."""

import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .hashing import SEPARATOR

HOW_TO_GENERATE = (
    "Gere uma chave com 'python manage.py generate_signing_key' "
    "e cole a linha AUDIT_SIGNING_KEY=... no arquivo backend/.env."
)


def anchor_payload(lot_id, bid_count: int, last_bid_hash: str) -> str:
    """O texto da âncora no formato fixo da especificação: "lot_id|bid_count|last_bid_hash"."""
    return SEPARATOR.join([str(lot_id), str(bid_count), last_bid_hash])


def generate_key_text() -> str:
    """Uma chave privada nova: os 32 bytes crus da chave Ed25519, em base64."""
    raw = Ed25519PrivateKey.generate().private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return base64.b64encode(raw).decode("ascii")


def _private_key() -> Ed25519PrivateKey:
    """Lê a chave privada de AUDIT_SIGNING_KEY. Vazia ou inválida: ImproperlyConfigured."""
    key_text = settings.AUDIT_SIGNING_KEY
    if not key_text:
        raise ImproperlyConfigured(f"AUDIT_SIGNING_KEY está vazia. {HOW_TO_GENERATE}")
    try:
        raw = base64.b64decode(key_text, validate=True)
        return Ed25519PrivateKey.from_private_bytes(raw)
    except ValueError as error:
        raise ImproperlyConfigured(
            f"AUDIT_SIGNING_KEY não é uma chave Ed25519 válida (base64 de 32 bytes). {HOW_TO_GENERATE}"
        ) from error


def sign_anchor(lot_id, bid_count: int, last_bid_hash: str) -> str:
    """Assina a âncora com a chave privada. Devolve a assinatura (64 bytes) em base64."""
    payload = anchor_payload(lot_id, bid_count, last_bid_hash).encode("utf-8")
    signature = _private_key().sign(payload)
    return base64.b64encode(signature).decode("ascii")


def verify_anchor(lot_id, bid_count: int, last_bid_hash: str, signature: str) -> bool:
    """Confere a assinatura com a chave pública. Vazia, ilegível ou falsa: False, nunca exceção."""
    if not signature:
        return False
    payload = anchor_payload(lot_id, bid_count, last_bid_hash).encode("utf-8")
    try:
        _private_key().public_key().verify(base64.b64decode(signature, validate=True), payload)
    except (InvalidSignature, ValueError):
        return False
    return True


def public_key_text() -> str:
    """A chave pública, para qualquer pessoa conferir as assinaturas: "ed25519:<base64 do DER>"."""
    der = _private_key().public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return f"ed25519:{base64.b64encode(der).decode('ascii')}"
