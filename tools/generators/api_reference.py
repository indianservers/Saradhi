"""Generate the route inventory from authoritative exported OpenAPI."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    spec = json.loads((ROOT / "packages/api_contracts/openapi.json").read_text())
    lines = [
        "# API reference",
        "",
        "Swagger UI: http://127.0.0.1:8000/docs. OpenAPI: http://127.0.0.1:8000/openapi.json.",
        "Generated request/response schemas are authoritative; no per-app response duplication.",
        "Collection limits are 1..100, cursors opaque, and sort/filter predicates are allowlisted.",
        "",
        "## Functional endpoints",
        "",
    ]
    count = 0
    for path, methods in spec["paths"].items():
        for method, value in methods.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            auth = (
                "Bearer plus resource/scope authorization."
                if value.get("security")
                else "Public transport; endpoint-specific rate/provider verification applies."
            )
            lines.append(
                f"- `{method.upper()} {path}` — "
                f"{value.get('summary', value['operationId'])}. {auth}"
            )
            count += 1
    lines += [
        "",
        "## Verification",
        "",
        "Use sample-requests.ps1 explicitly for registration/login, cart/checkout, "
        "merchant, pilot and support requests.",
        "No default privileged account exists. "
        "Provision only a named existing user via the local operator CLI.",
        "Complete real-database examples: tests/integration/helpers.py and test_vertical_slice.py.",
        "See api-security.md and error-contracts.md for authorization, precision, "
        "state and error behavior.",
        "Sandbox finance requires explicit enabling "
        "and never performs a real financial transaction.",
        f"Total documented HTTP operations: {count}.",
    ]
    (ROOT / "docs/api/api-reference.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {count} API operation references")


if __name__ == "__main__":
    main()
