# Pilot positioning

`GET /api/v1/ai/positioning/zones/{zone_id}/recommendations` combines the zone demand baseline with current citywide available-pilot count. Pilot profiles do not persist current authorized zone membership, so the API labels zone supply `unavailable` and avoids inventing a shortage count. Any recommendation is advisory; it does not direct or force a pilot to relocate.

Weather, shift schedules, breaks, zone-level pilot presence, travel time and incentives are not available as trusted features yet. Add those feature sources before evaluating positioning quality.
