# Phase 9 AI foundation audit

Audited the Phase 2.C code, schema, routes, local readiness snapshot and existing tests before adding Phase 9 code. The detailed implementation remains in `ai_platform/`, `backend/modules/ai`, and the existing `/api/v1/ai/*` routes. Migration 0010 created a separate `intelligence` schema for feature runs, forecasts, model versions, inference metadata and optimization recommendations; it does not duplicate authoritative commerce or finance records.

| Capability | Classification | Evidence / limit |
|---|---|---|
| Demand forecast | Deterministic baseline only | Same local weekday/hour average; cutoff-aware features and chronological backtest. No trained model. |
| ETA | Deterministic/routing integration | Delegates to Phase 2.B routing and falls back when route provider is unavailable. No learned ETA. |
| Preparation time | Deterministic rule only | Item-count and queue-depth estimate; no merchant preparation labels exist. |
| Dispatch | Deterministic advisory optimizer | Greedy one-to-one scoring, bounded task/candidate counts; route, time-window and zone constraints remain explicitly unevaluated. |
| Merchant/product recommendations | Deterministic baseline | Requires approved, accepting merchants, current price and sellable stock; no personalization labels. |
| Risk | Deterministic review signal | Delay rules; does not punish or automatically block an actor. |
| Pilot positioning | Deterministic citywide indicator | Current zone presence is not stored, so zone supply remains unavailable. |
| Model registry/evaluation | Partial lifecycle | Registry, metrics and demand backtest exist. No training, artifact validation, canary, rollback, drift job or production model. |
| Copilot / LLM | Newly available optional read-only gateway | Phase 2.C copilot was unavailable; Phase 9 adds a centralized, credential-optional-compatible gateway and six scoped read-only evidence paths. No arbitrary model tools. |
| Alerts, reconciliation, personalization, durable agent memory | Missing / partial | Existing risk signals and operational alerts are separate; no trained anomaly models, cross-user memory, recommendation profile controls or AI alert workflow. |
| App interfaces | Not yet integrated | Backend APIs exist, but Phase 9 does not yet add contextual AI UI to all six Flutter/Next.js applications. |

## Data and model honesty

The latest checked-in readiness snapshot is from 2026-10-26 and records development with 0 orders, 0 delivery outcomes, 0 ETA samples and 0 preparation labels. It excludes 1,704 test orders from training. These are the snapshot counts, not a fresh count for this implementation date. No trained model or model accuracy is claimed. See `data-readiness.json`, `phase-2c-completion.md`, and `phase-9-test-results.md`.

## Phase 9 changes in this iteration

- One optional gateway selects an operator-configured OpenAI-compatible or local endpoint. Disabled by default; no credential is required to start.
- Six role-specific, read-only assistant endpoints retrieve bounded, permission-checked evidence through application services and always have a deterministic fallback.
- Provider failure, timeout, invalid response, or Redis rate-limiter outage falls back to verified evidence. Agent requests cannot write business state.
- The current integration is a foundation, not Phase 9 completion. The six application UIs, draft-cart review flow, richer support policy summary, complete tool catalog, trained model lifecycle, background scheduling and anomaly workflows remain blockers.
