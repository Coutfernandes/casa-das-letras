"""O comprovante na API: o que qualquer pessoa com o link vê."""

from rest_framework import serializers

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
