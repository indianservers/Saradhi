"""Permit the named support role to receive central queue scope."""

from alembic import op

revision = "20261026_0014"
down_revision = "20261026_0013"
branch_labels = None
depends_on = None


def upgrade():
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
        "Central support queue assignments are active authority; revoke by forward policy"
    )
