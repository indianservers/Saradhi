# AI platform boundaries

ai_platform directories reserve gateway, agents, models, features, evaluations and prompts.
Backend ai context mediates application-level inference through provider-neutral ports.
No provider credentials, model hosting or autonomous administrative actions are implemented.

All tool calls carry the current principal, permitted organization/city/branch scope and
correlation ID. Authorization/ownership runs again at the tool's application-service boundary.
AI gets no raw SQL, unrestricted database credential, shell or universal admin role. Tool
allowlists, schema validation and action budgets restrict execution. Refunds, pricing changes,
dispatch overrides and financial operations need reviewed policies and appropriate human approval.

Separate offline forecasting/recommendation features from online transactional decisions.
Do not include customer PII or raw GPS traces in prompts by default. Apply redaction, consent,
retention, region and vendor controls. Treat retrieved text as untrusted data, never instructions.
Version prompts/models, store minimal audit evidence, measure hallucination, scope violations,
fairness, latency and cost before enabling tools. Evals must include cross-tenant requests,
prompt injection, revoked permissions and provider failure. No real customer datasets in Phase 1.
