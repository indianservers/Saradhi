# Phase 6.A fleet architecture audit

**Scope:** shared FastAPI/PostgreSQL logistics, Redis presence, AI forecasting/dispatch, and `apps/pilot_app`. This audit checks the Phase 2.B, Phase 2.C, and Phase 6 implementations against the Phase 6.A brief. “Critical” is reserved for a verified safety/security defect; broad missing product capability is classified High.

## Findings by severity

### Critical — fixed in this change

| Finding | Evidence and impact | Resolution |
|---|---|---|
| Pilot availability could strand committed work. | `PUT /pilots/{id}/availability` could set a pilot offline with offered/accepted/picked-up assignments. `POST /pilots/me/availability` allowed a break during assigned work. The offer-accept path did not recheck that the pilot remained operationally available after dispatch. | Both availability routes now block going offline with open offers or active work; break requires no open offer or active assignment. Accept now row-locks the pilot and requires a currently eligible state and remaining capacity. Added real PostgreSQL integration assertions. |

No other Critical security defect was verified in the reviewed flows. This is not a substitute for a dedicated penetration test.

### High — acceptance blockers

| Area | Current evidence | Consequence / next work |
|---|---|---|
| Route optimization and batching | Phase 2.C dispatch optimization is bounded, deterministic, greedy, and advisory, recommending at most one task per pilot. The shared route-provider interface supports route/matrix/ordering, but production is configured as `UnavailableRoutingProvider`. Existing route/stop/optimization tables have no pilot route-plan API or execution workflow. | No OR-Tools/CVRP-TW solution, pickup-before-delivery precedence plan, multi-merchant batch, detour/capacity/freshness constraints, dynamic route versions, polylines, or route notifications. Keep dispatch deterministic and do not silently batch tasks until a configured road matrix, authoritative task constraints, and policy approval exist. |
| ETA and navigation | `/deliveries/{id}/eta` uses the routing interface and labels provider source/confidence; deployment defaults to an unavailable provider. Pilot UI can open coordinates in Google Maps externally. | ETA may return 503; no in-app road map, route line, traffic update, or turn-by-turn navigation. The app displays provider results only when returned and otherwise identifies ETA as unavailable. |
| Pilot demand/supply advice | Phase 2.C has a seasonal-naive order forecast and operations-scoped positioning endpoint. Zone pilot supply is not persisted. This change adds a self-scoped pilot view for only the pilot’s explicitly authorized zones, caches forecast snapshots for 15 minutes, and exposes coarse demand bands without exact counts. | Demand is a deterministic, untrained baseline, not a confirmed order queue. Zone supply, travel time, shortages, and incentives remain unavailable; no automatic repositioning is made. |
| Shifts and capacity | Shared `pilot_shifts`, `pilot_service_zones`, and `pilot_capabilities` tables already exist. This change adds a read-only self view for active/next shift, remaining scheduled minutes, capabilities, and authorized zones. | No schedule preferences/write API, breaks, shift check-in/completion, end-of-shift assignment guard, handover/reassignment, or rest-policy configuration. The dispatch engine does not reject work that cannot finish before shift end. |
| Delivery verification / COD | The delivery API still completes through customer acknowledgment; there is no pilot OTP/proof verification or COD collection/reconciliation workflow. | Do not expose a pilot “delivered” action or claim cash/proof settlement. These require dedicated atomic, idempotent APIs and operations review. |
| Earnings and settlements | Pilot UI reads the existing immutable earnings ledger, but no earning posting path, offer estimate, payout status, incentive award, or dispute API was found. | Ledger display is incomplete and cannot provide settlement transparency. Never calculate authoritative pay in Flutter. |
| Operational incidents | Generic user-owned support tickets and a city incident table existed. This phase extends that shared incidents table with pilot/task/reporter/category/resolution links and adds self-report, own-history, city-scoped staff read, audited access, acknowledge, and resolve APIs. Declared emergencies and high-risk categories pause new offers until staff resolution. | No dedicated staff UI, automatic notification acknowledgment, or atomic incident-to-task reassignment exists. Staff must review and use the existing dispatch reassign operation separately. The generic delivery-failure endpoint still has no reason/return workflow. |

### Medium — operational reliability and fairness

| Area | Current evidence | Risk / next work |
|---|---|---|
| Dispatch fairness | Phase 2.B `DispatchStrategy` (`weighted-v1`) scores pickup distance plus active task count; city dispatch weights are versioned. It does not account for idle time, recent offers, rejection/expiry, travel effort, earnings opportunity, or historical allocation. | Repeated proximity advantages and popular-merchant concentration are possible. Add reviewable, privacy-safe decision metadata and evaluated fairness measures before changing scoring; keep safety/eligibility constraints hard. |
| GPS quality | Server validates consent, offset-aware recent timestamps, accuracy, monotonic sequence and timestamp, and a 70 m/s jump threshold. PostgreSQL latest location is authoritative; history has retention and a subject/time index; Redis is a fail-soft presence cache. Anomalous jumps are rejected, not treated as fraud. | No explicit duplicate digest, mock-location indicator, clock-drift review record, smoothing, anomaly queue, or battery-saver signal is available. `latest_location` can be refreshed more often than retained history. |
| Battery/data | Phase 6 previously streamed high-accuracy location with a 25 m filter while foreground. This change uses high accuracy/25 m while the pilot has accepted/picked-up work and medium accuracy/100 m while online idle. It remains foreground-only and sends immediately on resume. | This is an adaptive request policy, not a measured battery-saving claim. No physical-device battery, network, GPS quality, UI frame, or background-suspension measurements are available. |
| Offline recovery | Secure token refresh is available; offers and work are refreshed from server APIs and are not locally replayed. Only GPS sequence is persisted. Pickup and offer transitions reload authoritative state after response. | No durable offline work snapshot, approved route version API, pending-command ledger, or connectivity reconciliation UI. Never replay expired offers or invent local completion. |
| Real-time offers | Shared realtime WebSocket ticket endpoint and Redis/outbox exist; pilot app currently polls offers every 8 seconds. | No pilot offer WebSocket subscription/reconnect cursor or push notification integration in the app. Polling can delay awareness and add request load. |
| Assignment concurrency | Phase 2.B locks the task then eligible pilot rows, uses `SKIP LOCKED`, a partial unique active-task index, task versions, and expiry worker. Accept/reject also lock task before assignment. | Correctness is covered by integration tests, but high-contention throughput and multi-city fleet load are not benchmarked. |
| Platform configuration | Flutter uses secure storage, explicit location consent, foreground location permissions, and current shared APIs. | Flutter/Dart SDK and generated platform runners are absent in this checkout; no analyzer, native build, lifecycle, map, or visual QA could be run. |

### Low — usability and observability

- Route execution now focuses on the next stop/action, offers a compact expandable stop list, shows server ETA source/confidence/distance when available, and labels provider outages. No map is drawn because no production provider is configured.
- The pilot fleet outlook is clearly marked as advisory prediction, identifies model status/provenance, and does not expose company-wide supply or financial totals.
- The current route contract still returns one pickup/drop-off pair per assignment; it is not a multi-stop optimized route.
- Forecast bands use fixed display thresholds over the existing baseline. They are coarse presentation labels, not an incentive or dispatch policy.

## Current implementation in this phase

- `GET /api/v1/pilots/me/operations`: own shift, own capabilities, and own active city zones only.
- `GET /api/v1/pilots/me/supply-demand`: coarse forecasts for up to five zones explicitly authorized to the caller; no fleet-wide supply counts or exact order totals.
- Pilot route screen: one prominent context-sensitive navigation/pickup action and expandable stops; provider ETA is source-attributed and optional.
- Location stream changes frequency/accuracy tier based on active work. Background tracking remains disabled.
- Dispatch availability and acceptance safety guards cover pending offers, committed work, break entry, suspension, and pilot state.
- Typed pilot incident reports use the existing operations incident ledger; city-scoped staff access is audited and emergency state cannot return online until resolved.

## Required before full 6.A acceptance

1. Configure a licensed routing provider and validate route matrix, ETA, traffic attribution, provider failure, and quota behavior.
2. Add versioned route planning/execution using existing route tables, with proven hard constraints, a time budget, feasibility validation, and deterministic fallback. Obtain dispatch/compensation policy before auto-batching.
3. Add authorized shift lifecycle and end-of-shift completion/reassignment safeguards.
4. Add authenticated incident reporting and operations review/reassignment with sensitive-data scoping.
5. Add idempotent proof/COD and ledger/payable/incentive settlement workflows before expanding earnings UX.
6. Add measurable fairness review and fleet-scale/PostGIS concurrency benchmarks.
7. Run Flutter analysis, widget tests, Android/iOS builds, device GPS/battery tests, and target-mockup visual comparisons in a Flutter-enabled environment.
