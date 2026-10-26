# Routes and stop order

The current shared dispatch schema links one delivery task to one fulfillment unit and one active assignment. The pilot screen renders the authorized pickup and drop-off for each active assignment and preserves backend assignment order. It can open valid coordinates in an external maps app. This is a single-delivery stop pair, not a batched multi-order route.

No dispatch route-plan/reorder API, multi-stop batch assignment, route polyline, traffic provider, or in-app turn-by-turn SDK is configured. The app does not invent roads or allow local stop reordering. Google Maps URL launch is only an external-navigation fallback, subject to device/provider availability.
