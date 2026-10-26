"""Permit explicit city-wide assignment scope for city operations roles."""

from alembic import op

revision = "20261026_0015"
down_revision = "20261026_0014"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE identity.user_role_assignments "
        "DROP CONSTRAINT ck_user_role_assignments_scoped_assignment"
    )
    op.execute("""ALTER TABLE identity.user_role_assignments
        ADD CONSTRAINT ck_user_role_assignments_scoped_assignment CHECK
          ((city_id IS NULL AND branch_id IS NULL) OR organization_id IS NOT NULL
           OR (city_id IS NOT NULL AND branch_id IS NULL))""")
    op.execute("""CREATE OR REPLACE FUNCTION identity.guard_scoped_assignment()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE branch_org uuid; branch_city uuid; role_name text;
        BEGIN
          SELECT name INTO role_name FROM identity.roles WHERE id=NEW.role_id;
          IF NEW.organization_id IS NULL AND role_name NOT IN
             ('customer','delivery_pilot','platform_super_admin','support_agent')
             AND NOT (role_name IN ('city_manager','city_operator')
                      AND NEW.city_id IS NOT NULL AND NEW.branch_id IS NULL) THEN
            RAISE EXCEPTION 'Role requires organization scope' USING ERRCODE='23514';
          END IF;
          IF NEW.branch_id IS NOT NULL THEN
            SELECT organization_id,city_id INTO branch_org,branch_city
              FROM merchant.merchant_branches WHERE id=NEW.branch_id;
            IF branch_org IS DISTINCT FROM NEW.organization_id OR
               (NEW.city_id IS NOT NULL AND branch_city IS DISTINCT FROM NEW.city_id) THEN
              RAISE EXCEPTION 'Role assignment scope mismatch' USING ERRCODE='23514';
            END IF;
          END IF;
          RETURN NEW;
        END $$""")


def downgrade():
    raise RuntimeError(
        "City scope assignments are operational authority; revoke with reviewed forward policy"
    )
