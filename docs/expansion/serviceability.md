# Zone serviceability

Checkout revalidates active city, approved accepting branch, future branch window, local operating hours/holidays, temporary closure, fulfillment capability, destination city, configured zone/category/merchant area, capacity and PostGIS containment/distance. If PostGIS or boundary support is missing, delivery checkout returns a service error; it does not substitute straight-line distance. Pickup returns after branch/city/window/capability validation.

Dynamic peak restrictions, cross-zone road-time policies, checkout slot locks, zone boundary management UI and production spatial performance tests remain incomplete. See `backend/application/commerce.py` for the authoritative serviceability guard.
