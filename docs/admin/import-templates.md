# Current import template

`GET /api/v1/bulk/templates/branches` returns a CSV header. Required fields: `external_ref,brand_id,city_id,branch_name,latitude,longitude`. IDs must reference existing records in the caller’s authorized scope. `external_ref` is the source system’s stable branch identifier; it is globally unique for this importer.

A mapping step supports approved alternate headers only; extra columns are rejected to avoid storing unnecessary data. Template includes no legal registration, owner identity, bank/payout, KYC document, customer identity or password fields. No real data file or credentials are included. Product/customer/pilot templates will be added only with their verified domain flows.
