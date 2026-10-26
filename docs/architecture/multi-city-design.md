# Multi-country and multi-city scope

Use stable globally unique IDs and explicit country/city/zone/service-area ownership.
Organizations, brands and branches are distinct; an organization may operate across cities.
Authenticated tenant membership alone never implies access to every city or branch.
Every resource query must apply organization AND allowed geographic/branch scope as appropriate.

Store instants in UTC (PostgreSQL timestamptz); persist IANA timezone on geography/slot policy.
Resolve DST ambiguity and nonexistent local times explicitly. Localized display belongs to
clients. Currency belongs to each priced obligation; no cross-currency settlement arithmetic
without explicit FX records and reviewed rounding rules.

Service areas will use versioned polygons and PostGIS geography/geometry plus GiST indexes.
Validate polygon overlaps, coordinate system and geographic query plans before schema approval.
Check PostGIS availability but never install extensions without database-owner approval.
Regional partitioning is a future decision based on residency, latency and data volume;
keep region routing explicit, avoid early separate databases per city. Sensitive GPS retention
and exposure differ from durable delivery proof and order retention.
