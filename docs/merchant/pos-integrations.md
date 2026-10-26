# POS integration boundary

`backend/integrations/pos/contracts.py` defines immutable external references, sync checkpoints/results, and a vendor-neutral `PosAdapter` protocol for catalog, price, stock, order, acknowledgement, preparation, cancellation, and invoice-reference operations. The port does not make Quickbuddy inventory/order state dual-authoritative.

Local protocol-conformance smoke tests use a fixture only. There is no configured provider, credential lifecycle, external-ID persistence, job queue, webhook verifier, retry/dead-letter service, conflict policy, health dashboard, or live POS contract. Credentials must remain server-side. A provider implementation requires provider documentation and an explicit source-of-truth policy before activation. Protocol definitions alone are not a functioning POS integration.
