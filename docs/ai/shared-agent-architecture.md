# Shared AI agent architecture

`ai_platform/gateway` centralizes optional model selection, bounded prompts, output checks, timeout, concurrency and offline fallback. `backend/application/ai_agents.py` retrieves role-scoped evidence from existing business services. API handlers authenticate the current session, enforce organization/city/branch/ticket ownership through existing permission checks, then pass only the selected evidence to the gateway.

The six agent configurations are customer, merchant, pilot, city, admin and support. Their allowlists name only the read-only evidence tools currently implemented. There is no model-directed tool loop, SQL, shell, file, deployment or write access. No conversation history is persisted; only an input digest and inference metadata are recorded. The agent cannot confirm checkout, payment, refunds, dispatch, inventory edits, bank changes or finance postings.

Context is per request and expires with it. City, branch, organization and ticket identifiers are required where applicable; pilot identity comes from the authenticated user. Existing `scoped`, ownership and support assignment services remain the authority.
