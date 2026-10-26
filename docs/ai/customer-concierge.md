# Customer concierge

`POST /api/v1/ai/agents/customer/query` requires an active authenticated user and a selected active city. Its only evidence source is a live query of active products, variants, current prices, sellable stock and approved accepting branches. It returns actual matching catalog rows with price/currency and quantity, plus source metadata. It does not use order history, saved preferences or addresses.

This is read-only search and explanation. It does not draft or mutate a cart, make a recommendation from personal history, claim serviceability, place an order or initiate payment. Customer-facing reviewable cart tools and the Flutter panel remain to be built. Ordinary checkout/payment remains independent of AI.
