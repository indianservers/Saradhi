# AI copilot security

`GET /api/v1/ai/copilot/status` reports `unavailable` and no provider configured. `POST /api/v1/ai/copilot/query` returns 503. No prompt is sent to a provider, no tool executes, and no rule-based response is represented as an LLM answer.

Before enabling a provider, define typed allowlisted tools, validate JSON arguments and outputs, re-check the current user's effective organization/city/branch/resource permission on every tool call, treat merchant/customer content as untrusted, set strict timeouts, redact audit data, and require human approval for sensitive writes. Arbitrary SQL, order deletion, unrestricted refund, privilege changes and automated punitive actions must remain unavailable.
