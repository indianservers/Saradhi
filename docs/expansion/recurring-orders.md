# Recurring order schedules

Customers can create a daily, weekly or monthly schedule from their own open cart using `POST /api/v1/fulfillment/recurring-plans`. The service snapshots item/branch/quantity/method/address references, not a charge authorization or a committed order. Owner-scoped APIs list plans and occurrences, pause/resume/cancel plans, and skip local dates. Regulated and variable-weight items are excluded.

An ARQ worker expands active plans over a bounded 14-day horizon every 15 minutes. Occurrences and scheduling-job records are inserted idempotently. Each occurrence stays `awaiting_revalidation`; current prices, stock, merchants, address, delivery window and valid payment authorization must be checked before normal checkout. No recurring order or charge is generated automatically. DST-ambiguous/nonexistent local times fail for review rather than being shifted silently.
