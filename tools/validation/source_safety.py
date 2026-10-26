"""Small source hygiene check, not a comprehensive security scanner."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP = {
    ".secrets",
    ".local",
    ".git",
    ".venv",
    "node_modules",
    ".next",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    "quickbuddy_backend.egg-info",
}


def main():
    checked = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or SKIP.intersection(path.relative_to(ROOT).parts):
            continue
        if path.name.startswith(".env") and not path.name.endswith("example"):
            continue  # Local secrets are intentionally excluded from output.
        if path.suffix in {".pem", ".key"}:
            raise AssertionError(f"Private-key file in source: {path.relative_to(ROOT)}")
        if path.suffix not in {".py", ".ts", ".tsx", ".dart", ".json", ".yaml", ".yml", ".md"}:
            continue
        content = path.read_text(encoding="utf-8-sig")
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", content):
            raise AssertionError(f"Private key in {path.relative_to(ROOT)}")
        if path.suffix == ".py" and "domain" in path.parts:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    assert not (node.module or "").startswith(("fastapi", "sqlalchemy"))
        checked += 1
    print(
        f"PASS: {checked} source files checked for key material and domain import hygiene; "
        "not a guarantee of absence of all secrets"
    )


if __name__ == "__main__":
    main()
