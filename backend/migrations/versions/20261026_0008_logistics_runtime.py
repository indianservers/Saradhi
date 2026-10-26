"""Add bounded GPS metadata, pilot state, tracking tickets, policies and ETA history."""

from alembic import op

revision = "20261026_0008"
down_revision = "20261026_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE fulfillment.pilot_profiles
        ADD COLUMN state text NOT NULL DEFAULT 'offline',
        ADD COLUMN max_active_tasks integer NOT NULL DEFAULT 1,
        ADD COLUMN vehicle_type text NOT NULL DEFAULT 'bike',
        ADD CONSTRAINT ck_pilot_task_capacity CHECK (max_active_tasks BETWEEN 1 AND 5),
        ADD CONSTRAINT ck_pilot_state CHECK (state IN
          ('offline','online_available','offer_pending','assigned','on_break','unavailable','suspended'))""")
    op.execute("""ALTER TABLE fulfillment.pilot_latest_location
        ADD COLUMN accuracy_m numeric(20,4) NOT NULL DEFAULT 0,
        ADD COLUMN heading_degrees numeric(20,4),
        ADD COLUMN speed_mps numeric(20,4),
        ADD COLUMN client_sequence integer NOT NULL DEFAULT 0,
        ADD COLUMN battery_percent integer,
        ADD COLUMN app_state text NOT NULL DEFAULT 'foreground',
        ADD CONSTRAINT ck_location_accuracy CHECK (accuracy_m BETWEEN 0 AND 1000),
        ADD CONSTRAINT ck_location_heading CHECK (
          heading_degrees IS NULL OR heading_degrees BETWEEN 0 AND 360),
        ADD CONSTRAINT ck_location_speed CHECK (speed_mps IS NULL OR speed_mps BETWEEN 0 AND 100),
        ADD CONSTRAINT ck_location_battery CHECK (
          battery_percent IS NULL OR battery_percent BETWEEN 0 AND 100),
        ADD CONSTRAINT ck_location_app_state CHECK (app_state IN ('foreground','background'))""")
    op.execute("""ALTER TABLE fulfillment.pilot_location_events
        ADD COLUMN accuracy_m numeric(20,4) NOT NULL DEFAULT 0,
        ADD COLUMN heading_degrees numeric(20,4),
        ADD COLUMN speed_mps numeric(20,4),
        ADD COLUMN client_sequence integer NOT NULL DEFAULT 0,
        ADD COLUMN battery_percent integer,
        ADD COLUMN app_state text NOT NULL DEFAULT 'foreground'""")
    op.execute("""CREATE TABLE fulfillment.tracking_ws_tickets (
        id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES identity.users(id) ON DELETE RESTRICT,
        token_hash text NOT NULL UNIQUE, expires_at timestamptz NOT NULL,
        consumed_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now())""")
    op.execute("""CREATE INDEX ix_tracking_ws_tickets_expiry
        ON fulfillment.tracking_ws_tickets (expires_at)""")
    op.execute("""CREATE TABLE fulfillment.dispatch_policies (
        id uuid PRIMARY KEY, city_id uuid NOT NULL REFERENCES geo.cities(id) ON DELETE RESTRICT,
        version integer NOT NULL, weights jsonb NOT NULL,
        active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_dispatch_policies_city_id UNIQUE(city_id, version))""")
    op.execute("""CREATE UNIQUE INDEX uq_active_dispatch_policy_city
        ON fulfillment.dispatch_policies (city_id) WHERE active""")
    op.execute("""CREATE TABLE fulfillment.eta_estimates (
        id uuid PRIMARY KEY,
        task_id uuid NOT NULL REFERENCES fulfillment.delivery_tasks(id) ON DELETE RESTRICT,
        generated_at timestamptz NOT NULL, pickup_at timestamptz,
        delivery_at timestamptz NOT NULL, source text NOT NULL, confidence text NOT NULL,
        rule_version text NOT NULL, reason text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now())""")
    op.execute("""CREATE INDEX ix_eta_estimates_task_time
        ON fulfillment.eta_estimates (task_id, generated_at DESC)""")


def downgrade():
    raise RuntimeError(
        "Logistics runtime records are forward-only; use a reviewed repair migration"
    )
