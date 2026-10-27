"""O canal WebSocket da sala do lote."""

from urllib.parse import parse_qs

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from apps.accounts.models import User
from apps.accounts.tickets import redeem_ticket
from apps.auctions.models import Lot

from .events import lot_group, lot_snapshot, viewer_group

LOT_NOT_FOUND = 4404


class LotConsumer(JsonWebsocketConsumer):
    """Uma conexão aberta na sala de um lote. Visitantes assistem; o ticket só identifica quem está logado."""

    def connect(self):
        lot_id = self.scope["url_route"]["kwargs"]["lot_id"]
        lot = Lot.objects.select_related("item", "auctioneer", "leader", "winner").filter(id=lot_id).first()
        if lot is None:
            self.close(code=LOT_NOT_FOUND)
            return

        viewer = self._viewer_from_ticket()
        self.joined_groups = [lot_group(lot.id)]
        if viewer is not None:
            self.joined_groups.append(viewer_group(lot.id, viewer.id))
        for group in self.joined_groups:
            async_to_sync(self.channel_layer.group_add)(group, self.channel_name)

        self.accept()
        self.send_json(lot_snapshot(lot, viewer))

    def disconnect(self, code):
        for group in getattr(self, "joined_groups", []):
            async_to_sync(self.channel_layer.group_discard)(group, self.channel_name)

    def lot_event(self, event):
        """Repassa ao navegador um evento enviado a um dos grupos desta conexão."""
        self.send_json(event["payload"])

    def _viewer_from_ticket(self):
        """O usuário do ticket do endereço (?ticket=...), ou None para um visitante."""
        query = parse_qs(self.scope["query_string"].decode())
        user_id = redeem_ticket(query.get("ticket", [None])[0])
        if user_id is None:
            return None
        return User.objects.filter(id=user_id, is_active=True).first()