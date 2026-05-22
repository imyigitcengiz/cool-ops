from datetime import datetime, timezone

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def publish_live_event(kind, action="updated", object_id=None, message=None):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = {
        "type": "live_event",
        "kind": kind,
        "action": action,
        "id": object_id,
        "message": message or "Veriler güncellendi.",
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    async_to_sync(channel_layer.group_send)("live_updates", payload)
