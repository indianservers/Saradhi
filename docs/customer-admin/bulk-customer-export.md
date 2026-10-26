# Bulk customer export

`GET /api/v1/admin/customers-export` is a bounded, on-demand CSV export (maximum 500 rows) using the authorized city/order scope. It includes customer ID, name, status, **masked** email/phone, verification flags, order counts, historical gross purchase value and last-order time. It excludes addresses, exact contact values, payment identifiers and provider references. Formula-leading text is escaped; response is `private, no-store` and an audit event records row count and purpose.

This is a safe starter export, not the full Phase 12.A export job center: it has no private object storage, expiring URL, approval queue, scheduling or retention worker. Customer filters beyond city and name are not exposed.
