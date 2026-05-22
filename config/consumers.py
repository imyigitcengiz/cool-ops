from channels.generic.websocket import AsyncJsonWebsocketConsumer


class LiveSyncConsumer(AsyncJsonWebsocketConsumer):
    group_name = "live_updates"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def live_event(self, event):
        await self.send_json(
            {
                "kind": event.get("kind", "unknown"),
                "action": event.get("action", "updated"),
                "id": event.get("id"),
                "message": event.get("message", "Veriler güncellendi."),
                "ts": event.get("ts"),
            }
        )
