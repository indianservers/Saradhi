# Multi-merchant cart

The backend cart stores each line with its own branch, variant, quantity, optional customer address, delivery method and window. A single quote groups lines by merchant and fulfillment terms; order confirmation creates a parent order with merchant child orders. Existing PostgreSQL integration coverage verifies two merchants, two windows, child orders, reservations and idempotent confirmation.

The customer app persists one cart ID in secure storage and reloads cart state from the API. It can add current products from more than one branch, choose a window for each merchant line, optionally choose a saved-address courier method, update quantities with the current expected cart version, remove lines and request one consolidated quote.

Important constraints:

- Address/window/method is chosen at line creation. The API has no patch contract for changing those fields after adding a line.
- Pickup remains an available option; courier serviceability is backend-authoritative and can reject the quote.
- Quote is single-currency and server-limited to 100 lines.
- Backend does not return per-merchant fee/tax breakdown today.
- Branch and catalogue discovery expose cursor-based load-more controls. Cart requests a bounded set of up to 100 lines, matching the quote limit.
- A saved delivery choice can skip the add sheet only when its address and a currently returned window are still valid. Otherwise the customer selects a new choice.
