"""Add branch kitchen stations, dependent prep/packing tasks and task state versions."""

from alembic import op

revision = "20261026_0011"
down_revision = "20261026_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE merchant.kitchen_stations (
        id uuid PRIMARY KEY,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        branch_id uuid NOT NULL REFERENCES merchant.merchant_branches(id) ON DELETE RESTRICT,
        name text NOT NULL,
        is_packaging boolean NOT NULL DEFAULT false,
        max_concurrent integer NOT NULL DEFAULT 5,
        active boolean NOT NULL DEFAULT true,
        version integer NOT NULL DEFAULT 1,
        CONSTRAINT uq_kitchen_station_branch_name UNIQUE(branch_id, name),
        CONSTRAINT ck_kitchen_station_capacity CHECK(max_concurrent BETWEEN 1 AND 100)
    )""")
    op.execute("CREATE INDEX ix_kitchen_stations_branch_id ON merchant.kitchen_stations(branch_id)")
    op.execute("""CREATE TABLE commerce.kitchen_tasks (
        id uuid PRIMARY KEY,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        merchant_order_id uuid NOT NULL REFERENCES commerce.merchant_orders(id) ON DELETE RESTRICT,
        order_item_id uuid REFERENCES commerce.order_items(id) ON DELETE RESTRICT,
        branch_id uuid NOT NULL REFERENCES merchant.merchant_branches(id) ON DELETE RESTRICT,
        station_id uuid NOT NULL REFERENCES merchant.kitchen_stations(id) ON DELETE RESTRICT,
        task_key text NOT NULL,
        task_type text NOT NULL,
        label text NOT NULL,
        quantity numeric(20,4) NOT NULL DEFAULT 1,
        status text NOT NULL DEFAULT 'pending',
        version integer NOT NULL DEFAULT 1,
        target_completed_at timestamptz,
        started_at timestamptz,
        completed_at timestamptz,
        estimate_provenance text NOT NULL DEFAULT 'deterministic_rule',
        estimate_model_version text NOT NULL DEFAULT 'preparation-v1',
        CONSTRAINT uq_kitchen_task_order_key UNIQUE(merchant_order_id, task_key),
        CONSTRAINT ck_kitchen_task_type CHECK(task_type IN ('prep','packing')),
        CONSTRAINT ck_kitchen_task_status CHECK(
            status IN ('pending','in_progress','paused','completed')
        ),
        CONSTRAINT ck_kitchen_task_quantity CHECK(quantity > 0)
    )""")
    op.execute(
        "CREATE INDEX ix_kitchen_tasks_order_id ON commerce.kitchen_tasks(merchant_order_id)"
    )
    op.execute(
        "CREATE INDEX ix_kitchen_tasks_order_item_id ON commerce.kitchen_tasks(order_item_id)"
    )
    op.execute("CREATE INDEX ix_kitchen_tasks_branch_id ON commerce.kitchen_tasks(branch_id)")
    op.execute("CREATE INDEX ix_kitchen_tasks_station_id ON commerce.kitchen_tasks(station_id)")
    op.execute("CREATE INDEX ix_kitchen_tasks_status ON commerce.kitchen_tasks(status)")
    op.execute("""CREATE TABLE commerce.kitchen_task_dependencies (
        id uuid PRIMARY KEY,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        task_id uuid NOT NULL REFERENCES commerce.kitchen_tasks(id) ON DELETE RESTRICT,
        depends_on_task_id uuid NOT NULL REFERENCES commerce.kitchen_tasks(id) ON DELETE RESTRICT,
        CONSTRAINT uq_kitchen_task_dependency UNIQUE(task_id, depends_on_task_id),
        CONSTRAINT ck_kitchen_task_no_self_dependency CHECK(task_id <> depends_on_task_id)
    )""")
    op.execute(
        "CREATE INDEX ix_kitchen_task_dependencies_task_id "
        "ON commerce.kitchen_task_dependencies(task_id)"
    )
    op.execute(
        "CREATE INDEX ix_kitchen_task_dependencies_depends_on_task_id "
        "ON commerce.kitchen_task_dependencies(depends_on_task_id)"
    )
    # Preserve already accepted/preparing orders across rollout. Historical orders get
    # pending tasks and no invented target time; normal acceptance uses the live rule.
    op.execute("""INSERT INTO merchant.kitchen_stations
        (id, branch_id, name, is_packaging, max_concurrent, active, version)
        SELECT gen_random_uuid(), branches.branch_id, stations.name, stations.is_packaging,
               stations.max_concurrent, true, 1
        FROM (SELECT DISTINCT branch_id FROM commerce.merchant_orders
              WHERE status IN ('accepted', 'preparing')) branches
        CROSS JOIN (VALUES ('Main Kitchen', false, 8), ('Packaging', true, 4))
            AS stations(name, is_packaging, max_concurrent)
        ON CONFLICT (branch_id, name) DO NOTHING""")
    op.execute("""INSERT INTO commerce.kitchen_tasks
        (id, merchant_order_id, order_item_id, branch_id, station_id, task_key, task_type,
         label, quantity, status, version, estimate_provenance, estimate_model_version)
        SELECT gen_random_uuid(), item.merchant_order_id, item.id, child.branch_id, station.id,
               'legacy-item:' || item.id::text, 'prep',
               item.product_name || ' · ' || item.variant_name, item.quantity,
               'pending', 1, 'migration_backfill', 'legacy-open-order-v1'
        FROM commerce.order_items item
        JOIN commerce.merchant_orders child ON child.id = item.merchant_order_id
        JOIN merchant.kitchen_stations station
          ON station.branch_id = child.branch_id AND station.name = 'Main Kitchen'
        WHERE child.status IN ('accepted', 'preparing')""")
    op.execute("""INSERT INTO commerce.kitchen_tasks
        (id, merchant_order_id, order_item_id, branch_id, station_id, task_key, task_type,
         label, quantity, status, version, estimate_provenance, estimate_model_version)
        SELECT gen_random_uuid(), child.id, NULL, child.branch_id, station.id,
               'legacy-order:packing', 'packing', 'Final pack verification', 1,
               'pending', 1, 'migration_backfill', 'legacy-open-order-v1'
        FROM commerce.merchant_orders child
        JOIN merchant.kitchen_stations station
          ON station.branch_id = child.branch_id AND station.name = 'Packaging'
        WHERE child.status IN ('accepted', 'preparing')""")
    op.execute("""INSERT INTO commerce.kitchen_task_dependencies
        (id, task_id, depends_on_task_id)
        SELECT gen_random_uuid(), packing.id, preparation.id
        FROM commerce.kitchen_tasks packing
        JOIN commerce.kitchen_tasks preparation
          ON preparation.merchant_order_id = packing.merchant_order_id
        WHERE packing.task_type = 'packing' AND preparation.task_type = 'prep'
          AND packing.estimate_provenance = 'migration_backfill'
          AND preparation.estimate_provenance = 'migration_backfill'""")


def downgrade():
    raise RuntimeError(
        "Kitchen task history is operational audit data; use a reviewed forward migration"
    )
