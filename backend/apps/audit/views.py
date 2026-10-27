"""Rotas públicas da auditoria: o comprovante, a verificação do lote e a chave pública."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.auctions.models import Lot
from apps.auctions.settlement import settle_if_due

from .models import Receipt
from .serializers import AuditLotSerializer, ReceiptSerializer
from .signing import public_key_text
from .verification import verify_lot


class ReceiptView(APIView):
    """Um comprovante, aberto por quem tiver o link. Não precisa de login."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        receipt = get_object_or_404(
            Receipt.objects.select_related("lot__item", "lot__auctioneer"), public_token=token
        )
        return Response(ReceiptSerializer(receipt).data)


class PerIPScopedRateThrottle(ScopedRateThrottle):
    """O limite por escopo, contado sempre por IP, com ou sem login."""

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class AuditLotView(APIView):
    """A verificação de um lote. Pública: qualquer pessoa confere a cadeia de lances."""

    permission_classes = [AllowAny]
    throttle_classes = [PerIPScopedRateThrottle]
    throttle_scope = "audit"

    def get(self, request, lot_id):
        # Como na sala: quem audita um lote que já terminou vê o lote liquidado.
        settle_if_due(lot_id)
        lot = get_object_or_404(Lot.objects.select_related("item"), id=lot_id)
        result = verify_lot(lot)
        now = timezone.now()
        return Response(
            {
                "lot": AuditLotSerializer(lot, context={"now": now}).data,
                **result.as_dict(),
                "checked_at": now,
            }
        )


class PublicKeyView(APIView):
    """A chave pública do servidor, para conferir as assinaturas das âncoras por conta própria."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"algorithm": "Ed25519", "public_key": public_key_text()})
