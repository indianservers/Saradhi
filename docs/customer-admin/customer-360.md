# Customer 360

Company Admin reads a selected customer only after checking the caller's current `customer.read` grant and order scope. `/api/v1/admin/customers/{id}` returns masked contact, account status, registration time, bounded summary aggregates and explicit metric caveats. History is split into bounded `/orders`, `/payments`, `/addresses`, `/subscriptions`, `/loyalty`, `/referrals`, `/campaigns`, `/support`, `/feedback`, `/privacy` and `/security` reads. The web client loads a tab only when selected.

Exact address text/coordinates, payment provider references, review text and referral counterpart identities are omitted. `gross_purchase_value` sums historical order totals and does not deduct refunds or distinguish platform revenue; refunds appear separately. No attributable cost model exists, so lifetime contribution is returned as unavailable rather than estimated.

API pagination defaults to 25 and caps each history at 100. Customer summary endpoints currently provide bounded recent rows; next-page cursors are implemented for orders and directory but are not wired to UI controls yet.
