"""O canal WebSocket da sala do lote."""

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from apps.auctions.models import Lot

from .events import lot_group, lot_snapshot

LOT_NOT_FOUND = 4404


class LotConsumer(JsonWebsocketConsumer):
    """Uma conexão aberta na sala de um lote. Visitantes também podem assistir."""

    def connect(self):
        lot_id = self.scope["url_route"]["kwargs"]["lot_id"]
        lot = Lot.objects.select_related("item", "auctioneer", "leader", "winner").filter(id=lot_id).first()
        if lot is None:
            self.close(code=LOT_NOT_FOUND)
            return

        self.group = lot_group(lot.id)
        async_to_sync(self.channel_layer.group_add)(self.group, self.channel_name)
        self.accept()
        self.send_json(lot_snapshot(lot))

    def disconnect(self, code):
        if hasattr(self, "group"):
            async_to_sync(self.channel_layer.group_discard)(self.group, self.channel_name)

    def lot_event(self, event):
        """Repassa ao navegador um evento enviado ao grupo do lote."""
        self.send_json(event["payload"])
