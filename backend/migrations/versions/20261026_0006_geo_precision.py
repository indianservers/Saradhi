"""Preserve seven-decimal location history and optional city/province consistency."""

from alembic import op

revision = "20261026_0006"
down_revision = "20261026_0005"
branch_labels = None
depends_on = None


def upgrade():
    for table in ["geo.geo_locations", "fulfillment.pilot_location_events"]:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN latitude TYPE numeric(10,7), "
            "ALTER COLUMN longitude TYPE numeric(10,7)"
        )
    op.execute("""ALTER TABLE fulfillment.pilot_location_events ADD CONSTRAINT
        ck_pilot_location_events_rule_0 CHECK(latitude BETWEEN -90 AND 90
        AND longitude BETWEEN -180 AND 180)""")
    op.execute("""ALTER TABLE geo.cities ADD COLUMN state_province_id uuid,
        ADD CONSTRAINT fk_cities_state_province_id_states_provinces FOREIGN KEY(state_province_id)
        REFERENCES geo.states_provinces(id) ON DELETE RESTRICT""")
    for statement in HARDENING:
        op.execute(statement)


HARDENING = [
    """CREATE FUNCTION geo.guard_city_state() RETURNS trigger LANGUAGE plpgsql AS $$
       BEGIN
         IF NEW.state_province_id IS NOT NULL AND NEW.country_id IS DISTINCT FROM
            (SELECT country_id FROM geo.states_provinces WHERE id=NEW.state_province_id) THEN
           RAISE EXCEPTION 'City state country mismatch' USING ERRCODE='23514';
         END IF;
         RETURN NEW;
       END $$""",
    """CREATE TRIGGER city_state_scope BEFORE INSERT OR UPDATE ON geo.cities
       FOR EACH ROW EXECUTE FUNCTION geo.guard_city_state()""",
]


def downgrade():
    raise RuntimeError("Geographic precision and relationships require reviewed forward migration")
