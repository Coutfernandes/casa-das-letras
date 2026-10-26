"""
Pseudônimos públicos dos usuários.

Auditoria, comprovante e histórico da sala nunca mostram nome nem e-mail:
mostram um pseudônimo como "Licitante #a3f9c1". Ele é derivado do id do
usuário com HMAC, então é sempre o mesmo para a mesma pessoa, mas não dá
para descobrir o id (nem o usuário) a partir dele sem o ALIAS_SECRET.
"""

import hashlib
import hmac
from uuid import UUID

from django.conf import settings

ALIAS_PREFIX = "Licitante #"


def build_public_alias(user_id: UUID, length: int = 6) -> str:
    """Monta o pseudônimo a partir dos primeiros `length` caracteres do HMAC."""
    digest = hmac.new(
        key=settings.ALIAS_SECRET.encode(),
        msg=str(user_id).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"{ALIAS_PREFIX}{digest[:length]}"
