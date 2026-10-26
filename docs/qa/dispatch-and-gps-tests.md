# Dispatch, realtime and GPS verification

Existing API-backed integration coverage includes exclusive assignment acceptance, pickup/delivery transition versioning, stale/poor-accuracy location rejection, consent gating, incident handling, dispatch offer behavior, selected city authorization, WebSocket ticket and tracking service checks. The complete backend suite passed 95 tests.

No actual courier movement was fabricated. Tests used controlled fixture coordinates and fake/unavailable provider boundaries. No production GPS feed, maps provider, external routing, multi-node Redis fan-out, or live browser/mobile socket was exercised. Redis reconnect and transient-event snapshot recovery were not fault-injected. Freshness/fan-out and p95/p99 were not measured under representative concurrency.

Existing GPS smoke evidence explicitly describes sequential, one-pilot, single-process scope; it is not a fleet capacity claim. Remaining high-risk cases: out-of-order location, stale Redis presence after restart, 50 simultaneous acceptors, expired offer races, accepted-task reassignment, multi-stop route validity, and pilot restart/resume.
