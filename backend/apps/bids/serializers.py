"""O lance na API: o valor que o licitante envia e o lance aceito que volta."""

from rest_framework import serializers

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
