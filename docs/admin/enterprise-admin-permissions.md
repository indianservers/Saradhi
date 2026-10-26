# Enterprise admin permissions

The bulk branch importer checks current DB `merchant.write` assignments for each target brand/city. Job status, mapping, errors and cancellation are actor-owned; guessed job IDs return not found. Branch export uses the new DB permission `merchant.export` and rechecks organization/city/branch scope for every row. Role grant migration adds export only to platform super-admin, company-admin and city-manager roles; it does not trust token role names alone.

UI controls are not a security boundary. The same-origin Next proxy exposes only enumerated bulk routes and forwards only auth, idempotency/entity headers. CSV upload is capped to 5 MiB in both proxy and API. Additional tenant-isolation, CSRF, row-scope and privilege-escalation tests are required before broad rollout.
