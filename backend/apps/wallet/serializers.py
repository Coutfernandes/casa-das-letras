"""A carteira na API: o saldo, o extrato e o pedido de depósito."""

from rest_framework import serializers

from apps.auctions.serializers import LotSerializer

from .models import WalletEntry
from .services import MAX_DEPOSIT


class WalletEntrySerializer(serializers.ModelSerializer):
    lot_title = serializers.CharField(source="lot.item.title", default=None)

    class Meta:
        model = WalletEntry
        fields = ["id", "kind", "amount", "lot_title", "created_at"]
        read_only_fields = fields


class WalletSerializer(serializers.Serializer):
    """O saldo, os lotes que o comprometem e as últimas entradas do extrato."""

    total = serializers.IntegerField()
    committed = serializers.IntegerField()
    available = serializers.IntegerField()
    committed_lots = LotSerializer(many=True)
    entries = WalletEntrySerializer(many=True)


class DepositSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1, max_value=MAX_DEPOSIT)
