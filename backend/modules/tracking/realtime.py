"""Redis Pub/Sub fanout for transient live updates; REST snapshots remain authoritative."""

import asyncio
import json
import time
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect


async def publish(redis, topic: str, payload: dict, event_id: str | None = None):
    sequence_key = f"quickbuddy:realtime:sequence:{topic}"
    sequence = await redis.incr(sequence_key)
    await redis.expire(sequence_key, 86400)
    envelope = {"event_id": event_id or str(uuid4()), "sequence": sequence, "payload": payload}
    await redis.publish(f"quickbuddy:realtime:{topic}", json.dumps(envelope))
    return envelope


async def serve_socket(
    websocket: WebSocket,
    redis,
    topic: str,
    quota_key: str,
    max_connections: int,
    authorize=None,
):
    from time import monotonic

    member = str(uuid4())
    instant = time.time()
    count = await redis.eval(
        "redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1]); "
        "local n=redis.call('ZCARD', KEYS[1]); "
        "if n >= tonumber(ARGV[3]) then return n+1 end; "
        "redis.call('ZADD', KEYS[1], ARGV[2], ARGV[4]); "
        "redis.call('EXPIRE', KEYS[1], 120); return n+1",
        1,
        quota_key,
        instant - 120,
        instant,
        max_connections,
        member,
    )
    if count > max_connections:
        await websocket.close(code=1013, reason="connection_quota")
        return
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"quickbuddy:realtime:{topic}")
    await websocket.accept()
    last_activity = monotonic()
    last_authorization_check = monotonic()
    ping_window = time.time()
    ping_count = 0
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.25)
            if message and message.get("data"):
                await asyncio.wait_for(websocket.send_text(message["data"]), timeout=5)
                last_activity = monotonic()
                instant = time.time()
                await redis.zadd(quota_key, {member: instant})
                await redis.expire(quota_key, 120)
            try:
                incoming = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
            except TimeoutError:
                if monotonic() - last_activity > 90:
                    await websocket.close(code=1001, reason="heartbeat_timeout")
                    break
                if authorize and monotonic() - last_authorization_check >= 30:
                    if not await authorize():
                        await websocket.close(code=4403, reason="authorization_revoked")
                        break
                    last_authorization_check = monotonic()
                continue
            if len(incoming.encode()) > 4096:
                await websocket.close(code=1009, reason="message_too_large")
                break
            if incoming == "ping":
                if time.time() - ping_window >= 60:
                    ping_window, ping_count = time.time(), 0
                ping_count += 1
                if ping_count > 120:
                    await websocket.close(code=1008, reason="heartbeat_rate_limited")
                    break
                await websocket.send_json({"type": "pong"})
                last_activity = monotonic()
                instant = time.time()
                await redis.zadd(quota_key, {member: instant})
                await redis.expire(quota_key, 120)
            else:
                await websocket.send_json({"type": "error", "code": "unsupported_message"})
    except (WebSocketDisconnect, TimeoutError):
        pass
    finally:
        await pubsub.unsubscribe(f"quickbuddy:realtime:{topic}")
        await pubsub.aclose()
        await redis.zrem(quota_key, member)
