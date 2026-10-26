# ETA engine

ETA is versioned and stored per delivery task. The service requires a routing provider road duration and returns source, confidence, generated time and rule version; a materiality cooldown avoids recalculation on every location ping. Without a provider, the endpoint returns an explicit unavailable response. The deterministic fixture provider is used in integration tests. Current pilot-arrival timing is a straight-line heuristic and is not a road ETA; production ETA requires a configured road-routing provider and operational calibration.
