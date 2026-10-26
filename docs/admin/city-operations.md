# City operations

The City Operations `/workspace` page lists only cities returned by `/api/v1/operations/authorized-cities`, then shows active dispatch task IDs, backend statuses and versions, plus count totals for the selected city. It loads up to 50 active tasks per snapshot. It also shows pilot-reported incidents and supports acknowledge and resolve actions. Resolution requires an operator-entered summary (minimum 10 characters); the backend enforces city scope and the open → acknowledged → resolved state flow and writes audit/outbox events.

This endpoint intentionally returns no pilot roster, customer details, live GPS, candidate pilots, or map coordinates. Manual reassignment and map controls remain unavailable until a scoped dispatch/realtime API exists.
