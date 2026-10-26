"""Validate structural contract without claiming SDK compilation."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def validate():
    for name in ("customer_app", "pilot_app", "merchant_app"):
        base = ROOT / "apps" / name
        for file in ("pubspec.yaml", "lib/main.dart", "test/widget_test.dart", "README.md"):
            assert (base / file).is_file(), f"{name}/{file}"
        pubspec = (base / "pubspec.yaml").read_text()
        for shared in ("flutter_core", "flutter_design_system", "flutter_networking"):
            assert f"../../packages/{shared}" in pubspec
    for name in ("company_admin", "city_operations", "support_console"):
        assert (ROOT / "apps" / name / "package.json").is_file()
        assert (ROOT / "apps" / name / "app/(protected)/workspace/layout.tsx").is_file()
    print("PASS: six source projects and shared mobile dependencies; Flutter runners unvalidated")


if __name__ == "__main__":
    validate()
