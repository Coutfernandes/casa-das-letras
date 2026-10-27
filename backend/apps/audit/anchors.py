"""
A cópia externa das âncoras, no Redis (seção 7 da especificação).

Cada lance aceito acrescenta uma entrada no fim da lista "anchors:{lot_id}" (RPUSH).
A lista só recebe inserções. Sem REDIS_URL, a cópia fica desligada.
"""

import json
import logging
from functools import lru_cache

import redis
from django.conf import settings
from django.utils import timezone

from .signing import verify_anchor

logger = logging.getLogger(__name__)

# Tempo máximo, em segundos, esperando o Redis. Um Redis lento não segura o lance.
REDIS_TIMEOUT = 2


def anchors_key(lot_id) -> str:
    """A lista de âncoras de um lote no Redis."""
    return f"anchors:{lot_id}"


@lru_cache
def _connect(url: str) -> redis.Redis:
    """Um cliente por endereço, reaproveitado. Os testes trocam esta função pelo fakeredis."""
    return redis.Redis.from_url(
        url,
        decode_responses=True,
        socket_timeout=REDIS_TIMEOUT,
        socket_connect_timeout=REDIS_TIMEOUT,
    )


def get_client() -> redis.Redis | None:
    """O cliente do Redis, ou None quando a cópia está desligada (REDIS_URL vazia)."""
    if not settings.REDIS_URL:
        return None
    return _connect(settings.REDIS_URL)


def push_anchor(lot) -> bool:
    """Acrescenta a âncora atual do lote na lista. Diz se gravou. Uma falha aqui nunca desfaz um lance."""
    entry = {
        "bid_count": lot.bid_count,
        "last_bid_hash": lot.last_bid_hash,
        "signature": lot.anchor_signature,
        "created_at": timezone.now().isoformat(),
    }
    try:
        client = get_client()
        if client is None:
            return False
        client.rpush(anchors_key(lot.id), json.dumps(entry))
    except Exception:
        logger.exception("Não foi possível copiar a âncora do lote %s para o Redis", lot.id)
        return False
    return True


def all_anchors(lot_id) -> list[dict]:
    """Todas as âncoras do lote, da mais antiga para a mais nova. Desligada ou com erro: lista vazia."""
    try:
        client = get_client()
        if client is None:
            return []
        return [json.loads(item) for item in client.lrange(anchors_key(lot_id), 0, -1)]
    except Exception:
        logger.exception("Não foi possível ler as âncoras do lote %s no Redis", lot_id)
        return []


def last_anchor(lot_id) -> dict | None:
    """A âncora mais recente do lote, ou None (sem entradas, cópia desligada ou Redis fora do ar)."""
    try:
        client = get_client()
        if client is None:
            return None
        item = client.lindex(anchors_key(lot_id), -1)
    except Exception:
        logger.exception("Não foi possível ler a última âncora do lote %s no Redis", lot_id)
        return None
    return json.loads(item) if item else None


def restore_anchor(lot) -> bool:
    """
    Repõe a âncora atual do lote quando a cópia no Redis ficou para trás. Diz se repôs.

    Só repõe uma âncora com assinatura válida, e só quando a cópia tem MENOS lances que o lote.
    Uma cópia à frente do lote é sinal de retrocesso: repor por cima esconderia a prova.
    """
    if get_client() is None:
        return False
    if not verify_anchor(lot.id, lot.bid_count, lot.last_bid_hash, lot.anchor_signature):
        return False
    copied = last_anchor(lot.id)
    copied_count = int(copied["bid_count"]) if copied else 0
    if copied_count >= lot.bid_count:
        return False
    return push_anchor(lot)
