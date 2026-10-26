# Route batching

Financial orders and fulfillment tasks remain independent. The current optimization endpoint does not merge orders or create multi-stop routes; it recommends one task per pilot and leaves authoritative assignment to Phase 2.B. This avoids silently bundling unrelated deliveries.

Multi-restaurant batching is not enabled. The database and local infrastructure do not yet provide complete package/food compatibility, route travel-time matrices, customer time-window feasibility, maximum detour, or PostGIS serviceability inputs. A future solver must preserve pickup-before-drop-off precedence and every underlying task's separate state, refund and settlement lifecycle, and compare plans against the deterministic fallback before activation.
