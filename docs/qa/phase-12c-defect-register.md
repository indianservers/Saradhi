# Phase 12.C defect and risk register

| ID | Severity | Finding | Evidence/status | Disposition |
|---|---|---|---|---|
| QB12C-01 | P1 verification gap | `kitchen_operator` receives coarse `merchant.write`; brief requires denial of sensitive merchant finance, settlement, user, and role actions. | Grant confirmed in seeded DB/migration; no direct kitchen role endpoint matrix was executed, so exploitability is unconfirmed. | Open; release gate for enabling kitchen access until sensitive routes are directly tested or grant is narrowed. No speculative code change made. |
| QB12C-02 | P1 operational blocker | API readiness returns 503 when Redis is unavailable. | Existing API health check: live 200, ready 503; Redis port unavailable. | Environment blocker; start/configure Redis and rerun readiness/realtime tests. |
| QB12C-03 | P1 test coverage blocker | 14 catalog roles but only six identities/contexts including baseline customer exercised; no exhaustive role logins or direct action matrix. | Integration suite 47 pass; role coverage summarized in matrix. | Open; add scoped role fixtures and route-by-route allow/deny assertions. |
| QB12C-04 | P2 verification blocker | Flutter apps and authenticated browser experiences not functionally tested. | Flutter/Dart/adb/Android SDK and Playwright unavailable. | Open; provide toolchains/device/browser automation and test accounts. |
| QB12C-05 | P2 verification gap | Broad import/export formats and failure cases not individually certified in this phase. | Existing API/unit coverage ran as part of suite; no standalone exhaustive format/cancellation/expiry/UI campaign. | Open; add explicit scenario coverage. |

No defect was represented as fixed by this Phase 12.C work. No P0 defect was reproduced in executed tests; this is not proof of absence.
