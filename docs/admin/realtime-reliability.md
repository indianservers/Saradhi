# Realtime reliability

The admin data hook uses no-store REST reads and polls every 30 seconds; manual refresh is available. It aborts an in-flight request when the selected resource changes and reports errors instead of showing stale values as current.

Local capability health reports Redis unavailable and cross-instance events disabled. Therefore, WebSocket delivery, reconnect/backoff, event replay, and multi-instance consistency have not been verified or claimed. A future realtime transport needs sequence IDs, authorization on subscription, reconnect recovery, and polling fallback.
