"""Persist explicit, versioned pilot location consent and immutable history."""

from alembic import op

revision = "20261026_0009"
down_revision = "20261026_0008"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE fulfillment.pilot_profiles
        ADD COLUMN location_consent_at timestamptz,
        ADD COLUMN location_consent_version text,
        ADD CONSTRAINT ck_pilot_location_consent_pair CHECK
          ((location_consent_at IS NULL) = (location_consent_version IS NULL))""")
    op.execute("""CREATE TABLE fulfillment.pilot_location_consents (
        id uuid PRIMARY KEY,
        pilot_id uuid NOT NULL REFERENCES fulfillment.pilot_profiles(id) ON DELETE RESTRICT,
        policy_version text NOT NULL,
        accepted boolean NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now())""")
    op.execute("""CREATE INDEX ix_pilot_location_consents_history
        ON fulfillment.pilot_location_consents (pilot_id, created_at DESC)""")
    op.execute("""CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE
        ON fulfillment.pilot_location_consents FOR EACH ROW
        EXECUTE FUNCTION audit.deny_record_mutation()""")


def downgrade():
    raise RuntimeError("Consent history is forward-only; use a reviewed repair migration")
