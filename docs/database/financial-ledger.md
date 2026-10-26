# Financial ledger and sandbox boundary

A ledger book belongs to one legal entity, organization and currency. Accounts belong to a
book and carry an explicit asset/liability/equity/revenue/expense kind. Journal lines use
positive debits and negative credits. Every posted journal needs at least two nonzero lines
and must sum to zero independently for every currency. Mixed legal-entity books are rejected.
Decimal amounts must respect the currency's scale; ROUND_HALF_EVEN is the current explicit
rounding policy and must be reviewed for applicable tax/payment contracts before launch.

The service creates a draft header, inserts lines and marks it posted in one transaction.
A deferred PostgreSQL constraint trigger checks balance at commit, including direct SQL
which bypasses application validation. Database guards prohibit changing/deleting a posted
header, mutating its lines, adding lines after posting, or changing a used account/book identity.
Composite FKs enforce account/organization/currency and journal/organization scope. Corrections
are new reversal journals; original postings remain. Journal idempotency is organization/key,
and replay with different account amounts is rejected. API dependency teardown commits BEFORE
sending success, so deferred constraint failures cannot follow an already acknowledged write.

Account codes are explicit, not a universal default chart. Production accounting must separately
recognize customer receivables/collections, merchant and pilot payables, commissions, delivery
charges, promotion funding, taxes, gateway fees, refund liabilities, pilot cash and settlement
transfers. There is no cross-currency netting. Existing foundation tables hold reconciliations,
invoices, credit notes, payable/settlement/payout records and provider token references.
Automatic order-to-ledger accounting and production settlement execution are not implemented.
Do not treat an order total, payment status or Redis value as an authoritative account balance.

The deterministic SandboxGateway has no network/payment side effects and is disabled by default
and forbidden in production. All identifiers start SANDBOX:. Tests explicitly enable it with a
sandbox-only secret. HMAC verification authenticates exact webhook bytes; event IDs and payload
hashes deduplicate callbacks; amount/currency/state must match the locked payment intent.
Payment and order locking prevents a pending late callback from paying a cancelled order.
Repeated already-processed callbacks are acknowledged without producing another event.

Partial sandbox refunds require a merchant request, a different authorized finance approver,
and a matching approval amount/organization/order. Only one refund can consume an approval;
database guards and uniqueness enforce it. The payment row serializes refunds and cumulative
amounts cannot exceed the confirmed amount. Refund keys are scoped to payment and payload.
Multi-organization refunds are deliberately blocked until reviewed child allocations and
corresponding ledger/reconciliation rules are wired. No real charge, transfer or payout occurs.

Before production: approved chart of accounts and legal-entity policy; provider credential
adapter with signature verification; provider idempotency/reconciliation; allocation/refund
rules; settlement invariants; durable workflow recovery; finance access and separation of duties.
