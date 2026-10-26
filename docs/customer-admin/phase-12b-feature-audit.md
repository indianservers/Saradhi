# Phase 12.B customer administration feature audit

**Scope:** inspected identity, geo/address, commerce/order, finance/payment/refund, engagement, support, AI, Company Admin, customer Flutter sources, and the Phase 12.A bulk engine in this checkout on 2026-10-27. `PARTIAL` means some real foundation or a read path exists, not that the full requested workflow is complete. `VERIFIED` requires end-to-end evidence. The new Customer Admin endpoints have focused PostgreSQL integration tests for directory/360/order/export and access denial; every other feature is evaluated against existing source/tests rather than inferred from table presence.

| # | Capability | Status | Evidence and remaining gap |
|---:|---|---|---|
| 01 | Customer directory | PARTIAL | `GET /admin/customers`; customer role only, authorized city/order scope, masked contact; no saved views or full filter set. |
| 02 | Directory search and city scope | PARTIAL | Prefix name search and city filter; no zone/category/date/frequency filters. |
| 03 | Server-side cursor paging | PARTIAL | Keyset by UUID and bounded `limit`; cursor is not yet exposed as a next-page control in UI. |
| 04 | Configurable columns | MISSING | Fixed compact directory fields. |
| 05 | Saved customer views | MISSING | No saved filter definitions. |
| 06 | Privacy-safe customer export | PARTIAL | Audited, bounded 500-row CSV with formula escaping and masked contact; no central export job, approval, expiring file or retention. |
| 07 | Customer 360 overview | PARTIAL | Actual identity/order/payment-refund/loyalty summary, explicitly labels gross order value and unavailable contribution. |
| 08 | Customer order history | PARTIAL | Authorized, bounded order page; no page cursor UI or merchant/category drilldowns. |
| 09 | Payment and refund history | PARTIAL | Read-only bounded payment/refund data from finance tables; no detail UI test. |
| 10 | Address summary | PARTIAL | Label and city only; exact address and coordinates withheld. |
| 11 | Subscription history | PARTIAL | Existing subscription tables surfaced read-only; benefit/renewal analytics absent. |
| 12 | Loyalty balance and movements | PARTIAL | Existing loyalty accounts/transactions surfaced read-only; no earn/redeem/reversal admin workflow. |
| 13 | Referral history | PARTIAL | Existing referral records surfaced without counterpart identity. |
| 14 | Campaign redemption history | PARTIAL | Existing coupon redemption records surfaced; no CRM campaign console. |
| 15 | Support ticket history | PARTIAL | Ticket subject/status/date read within CRM customer scope; existing ticket conversation keeps separate support assignment controls. |
| 16 | Feedback history | PARTIAL | Review rating/moderation state surfaced without review body; no trend analytics. |
| 17 | Consent center | PARTIAL | New append-only self-service marketing consent ledger and read view; no access/correction/deletion requests, retention policy, or Flutter controls. |
| 18 | Customer security history | PARTIAL | Bounded authentication event summary and active session count; no admin session-revocation workflow. |
| 19 | Customer CSV import | MISSING | Phase 12.A importer accepts branches only. No customer identity creation/matching was added. |
| 20 | Customer XLSX import | MISSING | No XLSX parser or bounded workbook validation. |
| 21 | Duplicate review and safe import retry | MISSING | No customer staging candidates, review queue or identity conflict lifecycle. |
| 22 | Customer identity matching/merge | BLOCKED | No audited merge engine; automatic merge would risk historical ownership and identity records. |
| 23 | Governed account states | PARTIAL | Identity has active/suspended and verifier rejects non-active accounts; no full lifecycle state machine/admin correction flow. |
| 24 | Verification review | BLOCKED | Phone/email verification is customer challenge-based; no safe admin verification override. |
| 25 | Admin session revocation | MISSING | Sessions can be revoked by logout; no CRM-scoped revoke endpoint. |
| 26 | Customer profile correction | MISSING | No field-level reviewed correction process or history. |
| 27 | Reusable customer segments | PARTIAL | New bounded, typed allowlist rules for status/order count/gross value/dormancy/marketing consent; no saved definitions. |
| 28 | Segment preview and scheduled refresh | PARTIAL | Exact city-scoped count preview with consent state; no membership history or scheduled refresh. |
| 29 | RFM scoring | MISSING | No recency/frequency/monetary model or documented score bands. |
| 30 | Cohort and retention analytics | MISSING | No first/returning/dormant cohort read model. |
| 31 | Repeat interval/category migration analytics | MISSING | No aggregate pipeline or benchmark evidence. |
| 32 | Customer lifetime contribution / predictive CLV | BLOCKED | No attributable service/acquisition cost model or validated predictive training data. |
| 33 | Loyalty program operations | PARTIAL | Loyalty accounts and immutable transaction records exist; no admin rules/earn/redeem/reversal API. |
| 34 | Referral reward operations | PARTIAL | Referral program/records exist; no eligibility/reward administration workflow or duplicate-delivery test. |
| 35 | Subscription administration | PARTIAL | Membership records exist and are read-only visible; no admin plan/cohort/renewal controls. |
| 36 | Campaign approval and provider delivery | MISSING | No campaign state machine or messaging-provider integration; no live sends. |
| 37 | Consent-filtered campaign audience | BLOCKED | Consent evidence is absent; cannot safely target customers. |
| 38 | A/B experiment management | MISSING | No experiment/assignment/exposure model. |
| 39 | Acquisition source attribution | PARTIAL | Some source/attribution foundations exist; no governed CRM reporting and causal measurement. |
| 40 | Checkout funnel and abandonment intelligence | MISSING | No server-defined customer funnel read model. |
| 41 | Support/complaint analysis | PARTIAL | Actual ticket list is available; no SLA, repeat complaint, or trend analytics. |
| 42 | Refund and compensation approval | PARTIAL | Existing finance maker-checker approval engine is present; CRM does not create credits/refunds. |
| 43 | Customer satisfaction analytics | PARTIAL | Review/CSAT foundations exist; no combined rating trend dashboard. |
| 44 | Review moderation audit | PARTIAL | Moderation records exist; no dedicated CRM moderation workspace. |
| 45 | Data access/correction/deletion requests | BLOCKED | No privacy-request workflow or retention policy engine. |
| 46 | Customer CRM AI copilot | MISSING | Existing AI agents do not expose CRM customer-level tools/metrics. |
| 47 | Multi-country/city foundations | PARTIAL | Geo schema is multi-country; directory is city-scoped; locale, retention, and country policy differences absent. |
| 48 | Large-data performance | PARTIAL | Bounded SQL and schema indexes exist; no millions-row benchmark or aggregate read model. |
| 49 | Customer scope/audit controls | PARTIAL | DB permission, city/order scope, PII masking, export audit, and no-store responses; broad adversarial matrix remains. |
| 50 | Customer Flutter integration | PARTIAL | CRM reads the shared backend records; no Flutter app changes or customer-visible lifecycle/consent integration. |

**Status totals:** 0 VERIFIED, 31 PARTIAL, 14 MISSING, 5 BLOCKED. Do not interpret this as 50 completed capabilities. See the linked workflow notes and test evidence for limits.
