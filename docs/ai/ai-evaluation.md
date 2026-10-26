# AI evaluation

Existing unit tests cover cold-start forecast behavior, future-feature rejection, chronological evaluation metrics, and dispatch assignment uniqueness. Phase 9 adds gateway tests for role allowlists, PII/injection redaction, bounded provider requests, provider failure fallback and optional configuration. Integration tests exercise role scope and live evidence retrieval where the real local test database is available.

No model accuracy or production quality is inferred from fixtures. Missing coverage includes adversarial tool/context evaluation across every tenant boundary, load testing, provider cost evaluation, forecast interval coverage and domain-specific performance slices.
