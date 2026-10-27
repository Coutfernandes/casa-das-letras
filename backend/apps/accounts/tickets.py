"""Tickets curtos que identificam o usuário na conexão WebSocket."""

import secrets

from django.core.cache import cache

TICKET_SECONDS = 30
KEY_PREFIX = "ws-ticket:"


def issue_ticket(user) -> str:
    """Cria um ticket de uso único para o usuário, válido por 30 segundos."""
    token = secrets.token_urlsafe(24)
    cache.set(f"{KEY_PREFIX}{token}", str(user.id), TICKET_SECONDS)
    return token


def redeem_ticket(token: str | None) -> str | None:
    """Troca o ticket pelo id do usuário e o apaga. Devolve None se ele não vale mais."""
    if not token:
        return None
    key = f"{KEY_PREFIX}{token}"
    user_id = cache.get(key)
    if user_id is None:
        return None
    cache.delete(key)
    return user_id