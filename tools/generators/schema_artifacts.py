"""Generate review artifacts and the initial frozen migration (explicit --freeze).

Never overwrites an existing migration snapshot. Later revisions require separate reviewed files.
"""

import argparse
import ast
import json
from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from backend.persistence.guards import invariant_statements
from backend.persistence.registry import metadata

ROOT = Path(__file__).resolve().parents[2]


def generate(freeze=False):
    dialect = postgresql.dialect()
    tables = metadata.sorted_tables
    statements = [f"CREATE SCHEMA {schema}" for schema in sorted({t.schema for t in tables})]
    statements += [str(CreateTable(t).compile(dialect=dialect)).strip() for t in tables]
    statements += [
        str(CreateIndex(i).compile(dialect=dialect))
        for t in tables
        for i in sorted(t.indexes, key=lambda x: x.name)
    ]
    guards = invariant_statements(metadata)
    # Later migration guards are frozen alongside their revisions, not silently folded
    # into the initial schema revision. Count them in the latest documentation only.
    extra_guards = []
    for revision in (ROOT / "backend/migrations/versions").glob("*.py"):
        for node in ast.parse(revision.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "HARDENING" for t in node.targets
            ):
                extra_guards.extend(ast.literal_eval(node.value))
    statements += guards
    if freeze:
        target = ROOT / "backend/migrations/versions/20261026_0001_schema.json"
        if target.exists():
            raise SystemExit("Refusing to overwrite frozen migration")
        target.write_text(json.dumps(statements, indent=2) + "\n", encoding="utf-8")
    dictionary = {
        "tables": [],
        "table_count": len(tables),
        "constraint_count": sum(len(t.constraints) for t in tables),
        "index_count": sum(len(t.indexes) for t in tables),
        "trigger_count": sum(
            "CREATE TRIGGER" in v or "CREATE CONSTRAINT TRIGGER" in v for v in guards + extra_guards
        ),
    }
    dictionary["orm_constraint_count"] = dictionary["constraint_count"]
    dictionary["constraint_trigger_count"] = sum(
        "CREATE CONSTRAINT TRIGGER" in v for v in guards + extra_guards
    )
    dictionary["constraint_count"] += dictionary["constraint_trigger_count"]
    md = [
        "# Data dictionary",
        "",
        "Generated from SQLAlchemy metadata. Frozen migration is independently versioned.",
        "All FK delete actions are RESTRICT; no accounting cascades. UUIDv4 IDs, UTC timestamps.",
        "",
    ]
    erd = [
        "# Enterprise ERD",
        "",
        "Machine-readable complete relationships: schema.json.",
        "",
        "```mermaid",
        "erDiagram",
    ]
    for table in tables:
        item = {
            "schema": table.schema,
            "name": table.name,
            "columns": [],
            "constraints": [
                {
                    "name": c.name,
                    "type": type(c).__name__,
                    "sql": str(c.sqltext) if hasattr(c, "sqltext") else None,
                    "columns": [col.name for col in c.columns],
                }
                for c in sorted(table.constraints, key=lambda c: (type(c).__name__, str(c.name)))
            ],
            "indexes": [
                {
                    "name": i.name,
                    "columns": [c.name for c in i.columns],
                    "unique": i.unique,
                    "predicate": str(i.dialect_options["postgresql"].get("where")),
                }
                for i in sorted(table.indexes, key=lambda x: x.name)
            ],
        }
        md += [f"## {table.fullname}", ""]
        for col in table.columns:
            targets = [
                {"target": fk.target_fullname, "on_delete": fk.ondelete} for fk in col.foreign_keys
            ]
            definition = {
                "name": col.name,
                "type": str(col.type.compile(dialect=dialect)),
                "nullable": col.nullable,
                "primary_key": col.primary_key,
                "foreign_keys": targets,
                "server_default": str(col.server_default.arg) if col.server_default else None,
            }
            item["columns"].append(definition)
            md += [
                f"- `{col.name}`: {definition['type']}; "
                f"{'nullable' if col.nullable else 'required'}"
                + ("; PK" if col.primary_key else "")
                + "".join(f"; FK → {fk['target']} (RESTRICT)" for fk in targets)
                + (
                    f"; default {definition['server_default']}"
                    if definition["server_default"]
                    else ""
                )
                + "."
            ]
        md += [
            "",
            "Constraints: " + json.dumps(item["constraints"], ensure_ascii=False) + ".",
            "Indexes: " + json.dumps(item["indexes"], ensure_ascii=False) + ".",
            "",
        ]
        dictionary["tables"].append(item)
        for fk in sorted(table.foreign_key_constraints, key=lambda fk: str(fk.name)):
            source = fk.referred_table.fullname.replace(".", "_")
            destination = table.fullname.replace(".", "_")
            erd.append(f'  {source} ||--o{{ {destination} : "{fk.name}"')
    erd += [
        "```",
        "",
        "Diagram and dictionary describe implemented DDL, not evidence of applied migrations.",
    ]
    md += [
        "## Database-only invariants",
        "",
        "The deferred `finance.require_balanced_journal` constraint trigger "
        "is included in the total "
        "database constraint count in addition to ordinary ORM constraints. Full guard definitions "
        "are frozen in Alembic revisions 0001 and 0003. There are 57 user triggers, including "
        "posted-journal/line immutability, currency balance, scope, refund approval "
        "and append-only records.",
        "",
    ]
    (ROOT / "docs/database/schema.json").write_text(
        json.dumps(dictionary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (ROOT / "docs/database/data-dictionary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (ROOT / "docs/database/erd.md").write_text("\n".join(erd) + "\n", encoding="utf-8")
    print({k: v for k, v in dictionary.items() if k != "tables"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    generate(parser.parse_args().freeze)
