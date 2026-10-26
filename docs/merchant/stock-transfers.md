# Inter-branch stock transfers

No transfer request, approval, dispatch, receipt, damage, or cancellation API/table was added. Existing stock is branch-scoped, and its movement records are immutable audit evidence; they are not a transfer workflow. Destination stock must not be incremented by ad hoc adjustments to simulate a transfer. A future implementation needs legal-entity validation, source reservation, partial receipt accounting, movement linkage, retry idempotency, and explicit approval authority.
