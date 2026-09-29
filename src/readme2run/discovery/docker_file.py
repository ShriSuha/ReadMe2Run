from pathlib import Path


def find_dockerfile(repo_path: Path) -> str | None:
    """Return the relative Dockerfile path when one exists at the repo root."""
    for name in ("Dockerfile", "dockerfile"):
        path = Path(repo_path) / name
        if path.is_file():
            return name
    return None
