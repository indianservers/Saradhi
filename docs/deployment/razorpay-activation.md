# Razorpay activation gate

Razorpay remains disabled (`RAZORPAY_ENABLED=false`, mode `disabled`). No credentials or genuine gateway test transaction were supplied/performed. Deterministic simulated payment tests are not Razorpay sandbox evidence.

Activation requires account eligibility, owner approval, sandbox credentials from secret manager, app/API build compatibility, genuine test checkout, server-side signature/amount/currency verification, duplicate/out-of-order webhook tests, timeout recovery, refunds and reconciliation with ledger, alerting and support runbook. Keep test and live keys separate. Before live: review legal/finance, verify webhook URL/TLS, rotate keys, reconcile test evidence, set explicit live approval and perform staged low-value transaction under separate authorization. Never enable live by toggling mode alone; settings require production and explicit approval. Route/payout features are not implemented and settings reject activation.
