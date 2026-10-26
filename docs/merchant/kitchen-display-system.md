# Kitchen display system

The current KDS screen reads the same authorized branch queue as order management and renders active pending/accepted/preparing/ready orders with item names, quantities and variants. It refreshes every ten seconds, has a retry state and routes ticket actions to the backend order detail screen. It never marks work complete because a timer expired.

The backend currently models merchant-order state, not per-item/station work. Separate kitchen stations, item-ready aggregation, allergy/customer-note fields, prep estimate overrides, delayed-order reason, audible alerts, notification permissions and handover verification are outstanding. The existing screen is a basic live ticket list, not a complete restaurant KDS. Tablet columns, large touch targets, screen sizes and sound behavior need Flutter device validation.
