"""O lance na API: o valor que o licitante envia e o lance aceito que volta."""

from rest_framework import serializers

from apps.auctions.serializers import LotSerializer

from .models import Bid


class BidInputSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)


class BidSerializer(serializers.ModelSerializer):
    """Um lance como a sala e a auditoria mostram: só o pseudônimo, nunca nome ou e-mail."""

    bidder_alias = serializers.CharField(source="bidder.public_alias")

    class Meta:
        model = Bid
        fields = ["sequence", "amount", "bidder_alias", "created_at", "prev_hash", "hash"]
        read_only_fields = fields


class MyOpenBidSerializer(serializers.Serializer):
    """Um lote aberto em que o licitante deu lance. O lote vem com my_max_bid anotado."""

    lot = LotSerializer(source="*")
    my_max_bid = serializers.IntegerField()
    winning = serializers.SerializerMethodField()

    def get_winning(self, lot):
        return lot.leader_id == self.context["user"].id


class MyWonLotSerializer(serializers.Serializer):
    """Um lote que o licitante venceu, com o token do comprovante público."""

    lot = LotSerializer(source="*")
    final_price = serializers.IntegerField()
    closed_at = serializers.DateTimeField()
    bid_count = serializers.IntegerField()
    receipt_token = serializers.CharField(source="receipt.public_token")
