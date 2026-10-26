# Agent security controls

- Every query authenticates a current principal and checks active user status.
- Branch, city, organization and support-ticket scope is revalidated against database assignments on the request.
- Pilot access is resolved from the authenticated user's own pilot record.
- All agent tools are fixed, read-only context collectors; there is no arbitrary function calling, SQL, shell, file access or write tool.
- Question text is bounded and common direct identifiers are redacted before provider transmission. Raw conversation content and history are not persisted.
- Retrieved fields are bounded and treated as untrusted data. Product descriptions, support messages and delivery instructions are excluded.
- Provider/Redis failures use a deterministic evidence summary; they never block ordering or dispatch.
- High-impact actions are not exposed, so a model cannot self-approve or execute them.

Remaining security work includes adversarial red-team coverage for each data source, provider egress allowlisting, distributed rate-limit guarantees when Redis is unavailable, customer preference retention/deletion workflows, and explicit approval-backed write tools if such tools are added.
