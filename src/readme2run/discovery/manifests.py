from pathlib import Path

_MANIFEST_NAMES = (
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "uv.lock",
    "Cargo.lock",
)


def find_manifests(repo_path: Path) -> list[str]:
    """Return relative paths of known dependency and lock files."""
    root = Path(repo_path)
    found: list[str] = []
    for name in _MANIFEST_NAMES:
        path = root / name
        if path.is_file():
            found.append(name)
    return found
