# Multi-merchant payment allocation

The commerce schema splits a parent order into merchant orders, but Phase 8 does not yet persist captured payment allocations by child merchant and its tax/fee/discount components. The current Razorpay payment intent is for the parent order total. Cross-organization refund execution remains rejected by the existing refund service.

Before enabling multi-merchant payment settlement, persist immutable parent-to-child allocations, validate their sum against captured payment, separate each funding party/tax/fee/refund liability, and create one merchant payable per child. A rejection/refund for one child must not alter unrelated child settlement. Tests must cover rounding residuals, currencies, partial rejection, refund limits, and duplicate webhook delivery.
