"""Write an actual source tree, excluding dependency/build/cache output."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDE = {
    ".local",
    ".secrets",
    ".venv",
    "node_modules",
    ".next",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "quickbuddy_backend.egg-info",
}


def render(folder, prefix=""):
    entries = sorted(
        (
            p
            for p in folder.iterdir()
            if p.name not in EXCLUDE and not p.name.endswith(".tsbuildinfo")
        ),
        key=lambda p: (not p.is_dir(), p.name),
    )
    lines = []
    for index, entry in enumerate(entries):
        last = index == len(entries) - 1
        lines.append(
            prefix + ("`-- " if last else "|-- ") + entry.name + ("/" if entry.is_dir() else "")
        )
        if entry.is_dir():
            lines.extend(render(entry, prefix + ("    " if last else "|   ")))
    return lines


if __name__ == "__main__":
    target = ROOT / "docs/operations/source-tree.txt"
    target.touch(exist_ok=True)
    target.write_text("Quickbuddy/\n" + "\n".join(render(ROOT)) + "\n", encoding="utf-8")
    print(target.relative_to(ROOT))
