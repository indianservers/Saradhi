# Bulk export architecture (current scope)

`POST /api/v1/bulk/exports` currently exports up to 500 branches for a selected city as an on-demand UTF-8 CSV response. `merchant.export` is checked against live organization/city/branch assignments. Sensitive customer, payment, KYC and settlement columns are absent. Text columns are prefixed when they begin with spreadsheet formula characters. Export action is audited and response caching is disabled.

This endpoint is a synchronous small-result exception; it does not create a persisted export job, downloadable object, expiring link, schedule or central history. It does not support JSON/XLSX/PDF. No customer exports are exposed. Add private object storage, column-level authorization, expiry, access audit and retention before larger or sensitive exports.
