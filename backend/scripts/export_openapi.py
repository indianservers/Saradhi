import json
from pathlib import Path

from backend.api.app.main import create_app

if __name__ == "__main__":
    path = Path("packages/api_contracts/openapi.json")
    path.write_text(json.dumps(create_app().openapi(), indent=2) + "\n", encoding="utf-8")
    print(path)
