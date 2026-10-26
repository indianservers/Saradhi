# Live tracking

Pilot GPS identity is derived from the authenticated principal. A pilot must record versioned location consent before ingestion. Coordinates, accuracy, heading, speed, observation time, sequence, battery and app state are validated. Older/repeated points are ignored; implausible jumps are quarantined for review. PostgreSQL stores the latest point and sampled history with configured retention; Redis GEO is a hot cache after commit.

Freshness and history sampling are configurable. Offline state stops dispatch eligibility and consent revocation clears cached presence best-effort. Customer tracking is owner-scoped and reveals a fresh pilot position only after a task is assigned. Redis/PostGIS are unavailable locally, so live cache and spatial behavior are code paths, not validated runtime capabilities. Background GPS intervals depend on mobile OS policy and are not guaranteed.
