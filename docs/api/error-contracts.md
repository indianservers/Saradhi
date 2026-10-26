# Error contracts

All errors use {"error":{"code":"stable_code","message":"safe explanation","request_id":"correlation"}}.
X-Request-ID is echoed after bounded character validation or generated as UUID. No validation
input, password/OTP/token, raw SQL, connection URL, traceback or private document is returned.

401: invalid/missing access or refresh credentials, consumed/expired OTP; WWW-Authenticate Bearer.
403: wrong organization/city/branch/owner, unauthorized roles, missing separate financial approval.
404: missing resource. Some owned resources return 403 after retrieval; IDs are opaque UUIDs.
409: stale expected version, invalid transition, depleted stock/slot, reused idempotency payload,
expired quote, constraint conflict or transaction_retry. 40P01/40001 require retrying the whole
transaction with the original idempotency key, not blindly repeating an external effect.
422: invalid input, precision/currency or journal balance, invalid time range/cursor.
429: committed auth/OTP throttling; Retry-After 60. 503: unavailable DB, unconfigured local auth,
OTP or sandbox provider, PostGIS/spatial setup unavailable. Sandbox is forbidden in production.

Readiness is a documented exception to the business error envelope: health/ready returns a
Health payload with status and postgresql/redis dependency states and HTTP 200 or 503.
Health/live checks only process responsiveness. Redis remains unavailable locally, so readiness
is 503 even while PostgreSQL and the database-backed business/worker operations function.
