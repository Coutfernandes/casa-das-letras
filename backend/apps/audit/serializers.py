"""O comprovante e a auditoria na API: o que qualquer pessoa vê, sem login."""

from rest_framework import serializers

from apps.auctions.models import Lot

from .models import Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    """Comprovante público. Do vencedor, só o pseudônimo: nunca nome, e-mail ou id."""

    token = serializers.CharField(source="public_token")
    lot_id = serializers.UUIDField()
    title = serializers.CharField(source="lot.item.title")
    authors = serializers.ListField(source="lot.item.authors", child=serializers.CharField())
    first_publish_year = serializers.IntegerField(
        source="lot.item.first_publish_year", allow_null=True
    )
    closed_at = serializers.DateTimeField(source="lot.closed_at")
    bid_count = serializers.IntegerField(source="lot.bid_count")
    auctioneer_name = serializers.CharField(source="lot.auctioneer.name")

    class Meta:
        model = Receipt
        fields = [
            "token",
            "lot_id",
            "title",
            "authors",
            "first_publish_year",
            "winner_alias",
            "amount",
            "closed_at",
            "bid_count",
            "auctioneer_name",
            "issued_at",
            "last_bid_hash",
        ]
        read_only_fields = fields


class AuditLotSerializer(serializers.ModelSerializer):
    """O lote na página de auditoria: o livro, as datas e quantos lances recebeu."""

    title = serializers.CharField(source="item.title")
    authors = serializers.ListField(source="item.authors", child=serializers.CharField())
    first_publish_year = serializers.IntegerField(source="item.first_publish_year", allow_null=True)
    phase = serializers.SerializerMethodField()

    class Meta:
        model = Lot
        fields = [
            "id",
            "title",
            "authors",
            "first_publish_year",
            "phase",
            "starts_at",
            "ends_at",
            "closed_at",
            "bid_count",
        ]
        read_only_fields = fields

    def get_phase(self, lot):
        return lot.phase_at(self.context.get("now"))
