"""Enterprise schema with financial, scope and immutable-record guards.

The DDL snapshot is frozen in this revision directory; runtime model edits never rewrite it.
Downgrade intentionally refuses to delete business data.
"""

import json
from pathlib import Path

from alembic import op

revision = "20261026_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    statements = json.loads(
        Path(__file__).with_name("20261026_0001_schema.json").read_text(encoding="utf-8")
    )
    for statement in statements:
        op.execute(statement)


def downgrade():
    raise RuntimeError("Destructive downgrade requires explicit review; use backup/forward repair")
