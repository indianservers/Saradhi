"""Redis Pub/Sub adapter for committed outbox events. Recovery comes from REST snapshots."""

from backend.modules.tracking.realtime import publish


class RedisEventPublisher:
    def __init__(self, redis):
        self.redis = redis

    async def publish(self, event_id, aggregate_id, event_type, payload_version, payload):
        message = {
            "event_id": event_id,
            "aggregate_id": aggregate_id,
            "event_type": event_type,
            "payload_version": payload_version,
            "payload": payload,
        }
        topics = {f"delivery:{aggregate_id}"}
        order_id = payload.get("order_id")
        if order_id:
            topics.add(f"order:{order_id}")
        elif event_type.startswith("order."):
            topics.add(f"order:{aggregate_id}")
        for field, kind in (
            ("pilot_id", "pilot"),
            ("organization_id", "merchant"),
            ("city_id", "city"),
        ):
            value = payload.get(field)
            if value:
                topics.add(f"{kind}:{value}")
        for topic in sorted(topics):
            await publish(self.redis, topic, message, event_id=event_id)
