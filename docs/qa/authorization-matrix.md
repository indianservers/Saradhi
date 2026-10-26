# Authorization matrix

Repository review and available local integration tests (2026-10-27). This matrix is a partial test record, not exhaustive permission certification.

| Actor/resource | Enforced boundary observed | Negative evidence / status |
|---|---|---|
| Customer → order/cart/payment | `owned()` and customer identity checks; payment intent requires confirmed owner order | Existing integration suite exercises cross-owner access in selected commerce flows; not all nested resources/exports tested |
| Merchant staff → branches/catalogue/settlement | Current DB `RoleAssignment`, permission, membership, org/city/branch scope via `scoped()` / `branch_scope()` | Finance queue test denies unrelated user; full Merchant A vs B catalogue/settlement matrix incomplete |
| Pilot → assignment/task/location/earnings | Pilot profile derives from authenticated subject; assignment and state/version checks in logistics service | Exclusive assignment integration coverage exists; exhaustive Pilot A/B transition races not run |
| City operator → city operations | DB assignment city scope and permission checks | Cross-city integration tests cover selected operational views; exports and every filter not exhaustively tested |
| Support agent → support tickets | Scoped support permission, ticket claim/resolution workflow and audit | Existing support integration workflow passes; no exhaustive property-level testing |
| Finance viewer / approver → payouts/refunds | Finance permission and separate approval/execution paths | Refund approval queue scope integration exists; settlement posting race and payout authorization matrix remain open |
| Ordinary admin → super-admin grant | Database role assignment and scoped authorization, DB trigger validates assignment scope | Direct privilege-escalation fuzz/mass-assignment tests not run |
| AI agent → business tools | Defined tool registry and server-side API actor context inspected | No adversarial prompt/tool-argument authorization test executed; must be treated as unverified |
| External partner → internal APIs | No broad partner public API found in current inventory | Not applicable to enabled surface; future external API needs separate identity, scope and quota assessment |
| WebSocket subscriber → topic | Consumed one-time short-lived ticket; owner/assignment/current DB role authorization; periodic authorization recheck | Source reviewed, no live Redis/WebSocket cross-tenant E2E run |

Core deny-by-default behavior in `scoped()` checks active user and current database grants; token role claims alone do not satisfy this check. SEC-01 production auth configuration gap is fixed and retested. Open systematic matrix testing is a production gate blocker.
