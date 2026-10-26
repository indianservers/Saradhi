# Recommendations

`POST /api/v1/ai/recommendations/merchants` returns approved, accepting branches in an active city, optionally filtered by an explicit category-to-service-area mapping, and ranks by 30-day distinct-order popularity. `/products` filters to active products, current branch prices and sellable inventory. Both return organic deterministic results and explicitly report that personal history was not used.

No click/conversion labels or sufficient personalized history are available. There is no collaborative filtering or ranking model. Recommendation outputs cannot override serviceability, stock, pricing or merchant availability.
