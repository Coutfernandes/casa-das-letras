"""Lotes na API: o que a vitrine e o painel recebem, e o que o painel envia ao criar."""

from rest_framework import serializers

from apps.catalog.serializers import CatalogBookSerializer

from .models import Lot


class LotSerializer(serializers.ModelSerializer):
    """Um lote como a vitrine, a sala e o painel mostram. Nunca expõe nome nem e-mail de licitantes."""

    title = serializers.CharField(source="item.title")
    authors = serializers.ListField(source="item.authors", child=serializers.CharField())
    first_publish_year = serializers.IntegerField(source="item.first_publish_year", allow_null=True)
    cover_url = serializers.CharField(source="item.cover_url", allow_null=True)
    auctioneer_name = serializers.CharField(source="auctioneer.name")
    leader_alias = serializers.CharField(source="leader.public_alias", default=None)
    winner_alias = serializers.CharField(source="winner.public_alias", default=None)
    minimum_next_bid = serializers.IntegerField()
    phase = serializers.SerializerMethodField()

    class Meta:
        model = Lot
        fields = [
            "id",
            "title",
            "authors",
            "first_publish_year",
            "cover_url",
            "description",
            "auctioneer_name",
            "phase",
            "starting_price",
            "min_increment",
            "current_price",
            "minimum_next_bid",
            "bid_count",
            "leader_alias",
            "starts_at",
            "ends_at",
            "original_ends_at",
            "winner_alias",
            "final_price",
            "closed_at",
        ]
        read_only_fields = fields

    def get_phase(self, lot):
        # Um só "agora" por requisição: todos os lotes da lista usam o mesmo instante.
        return lot.phase_at(self.context.get("now"))


class LotCreateSerializer(serializers.Serializer):
    """O que o painel envia para criar um lote. Valores em centavos."""

    book = CatalogBookSerializer()
    description = serializers.CharField(max_length=1000, allow_blank=True, default="")
    starting_price = serializers.IntegerField(min_value=1)
    min_increment = serializers.IntegerField(min_value=1)
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()


class LotFilterSerializer(serializers.Serializer):
    """Parâmetros da vitrine: ?phase=live&q=machado&min_price=0&max_price=200000."""

    phase = serializers.ChoiceField(choices=["live", "scheduled", "finished"], default="live")
    q = serializers.CharField(max_length=200, required=False, allow_blank=True)
    min_price = serializers.IntegerField(min_value=0, required=False)
    max_price = serializers.IntegerField(min_value=0, required=False)