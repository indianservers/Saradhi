# PostGIS blocker and explicit installation requirements

The reused PostgreSQL 17.11 Windows distribution exposes pgcrypto, pg_trgm and btree_gist
control files but no PostGIS extension. None of those optional extensions was installed.
The isolated databases work for non-spatial features. No geography is approximated by circles,
city labels or hand-written coordinate math. Courier checkout returns spatial_unavailable 503.

An operator must obtain an official PostGIS build compatible with this exact PostgreSQL major,
Windows x64 ABI/distribution and required dependencies (GEOS/PROJ). Do not copy a random DLL or
assume a separate vendor install is binary-compatible. Alternatively select a managed PostgreSQL
provider/region with confirmed PostGIS support. This work is not an instruction to alter the
unrelated 5432 installation or to install anything globally without authorization.

After authorized installation, a database owner must verify pg_available_extensions, then use
a reviewed Alembic revision in backend/migrations to CREATE EXTENSION postgis, add a nullable
geometry(MultiPolygon,4326) boundary to geo.delivery_service_areas, validate polygons and add
GiST(boundary). Add spatial geometry/indexes for versioned zone boundaries as the query design
requires. Backfill and validate boundaries before setting spatial_ready=true. A reference design
SQL is in database/design/postgis-reference.sql; it is NOT a second executable migration history.

Serviceability's prepared SQL requires ST_Covers for the destination, ST_DWithin on geography
for the branch/destination maximum-distance policy, active city/zone/category, branch area/method,
branch hours/closures, future window and capacity. Configure zone_delivery_policies and
zone_capacity_settings and enabled categories; simply installing PostGIS does not make an area
serviceable. Before courier rollout add spatial boundary integration tests, reviewed capacity
admission rules and query-plan evidence. Current spatial SQL has not been executed locally.
