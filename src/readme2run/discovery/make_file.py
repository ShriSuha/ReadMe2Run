import re
from pathlib import Path

_TARGET = re.compile(r"^([A-Za-z0-9_.-]+)\s*:", re.MULTILINE)


def find_makefile_targets(repo_path: Path) -> list[str]:
    """Return Makefile target names when a Makefile is present."""
    for name in ("Makefile", "makefile"):
        path = Path(repo_path) / name
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            return [m.group(1) for m in _TARGET.finditer(text) if not m.group(1).startswith(".")]
    return []
