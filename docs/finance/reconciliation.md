# Financial reconciliation

The newly added authenticated Razorpay webhook inbox stores event ID, event type, payload hash, payment/provider references, status, and processing time. It does not retain raw webhook bodies or secrets. It detects duplicate event IDs with body conflicts and preserves unmatched valid payment references for later investigation.

Captured payments are correlated to provider order, amount, currency, internal intent, and capture reference. Checkout callbacks independently fetch provider status before confirmation. A payment-captured event may arrive after an authorization event; captured is terminal for this flow and older authorization/failure events do not downgrade it.

Gateway settlement files, bank statements, provider fee comparisons, refund reconciliation, cash deposits, and journal-to-provider reconciliation reports are not implemented.
