# Pilot earnings

`GET /api/v1/pilots/me/earnings` reads immutable `fulfillment.pilot_earnings` rows for the authenticated user's pilot profile and returns amount, currency, task reference, and record timestamp. The app displays these ledger records without deriving a wallet balance. Offer payout estimates, incentives, tips, pending settlement totals, paid payout status, and bank details are not available from this API and are not fabricated.

The current codebase contains the earnings table but no earning-posting path was found in this audit. Empty history means no records are present; it does not imply a payout balance of zero or a settlement state.
