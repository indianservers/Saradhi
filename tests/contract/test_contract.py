import json
from pathlib import Path

from backend.api.app.main import create_app


def test_export_has_no_drift():
    exported = json.loads(Path("packages/api_contracts/openapi.json").read_text())
    assert exported == create_app().openapi()
