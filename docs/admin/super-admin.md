# Super Admin control tower

The Company Admin `/workspace` page now uses live, selected-city API snapshots for dispatch counts, verified fleet aggregates, pilot incidents, approved branches, and registered AI model versions. City selection is a query parameter to the API, never an authorization boundary. Dispatch, fleet, and incident APIs enforce the caller's database-backed city scope.

The dashboard refreshes each bounded REST snapshot every 30 seconds and offers a manual refresh. It has honest loading, empty, API error, and scope-denied states. It contains no preview/sample orders, pilot identities, merchant activity, KPI figures, or charts.

The delivered view is not a global finance/customer/order control tower. Those aggregate/reporting endpoints do not exist yet; see [integration audit](phase-7-integration-audit.md).
