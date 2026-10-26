# ETA prediction

`POST /api/v1/ai/eta/predict` delegates to the Phase 2.B ETA service and logs prediction provenance. It uses a configured road-routing provider when one exists and returns an explicit unavailable response when it does not. Fresh assigned-pilot GPS may contribute a provider route to pickup. Merchant readiness and handling buffers remain deterministic rules.

There are no historical prediction-versus-actual labels sufficient to train or validate an ETA residual model. No confidence interval or lateness probability is fabricated. The local maps provider is unavailable; use the deterministic fixture only in tests. Existing ETA caching prevents recomputation for every GPS ping.
