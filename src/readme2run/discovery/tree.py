from pathlib import Path

from readme2run.configurations.loader import Settings, load_settings


def list_tree(repo_path: Path, settings: Settings | None = None, *, max_depth: int = 4) -> list[str]:
    """Walk the checkout and return relative paths, skipping .git.

    Stops after the tree cap from settings. Depth 0 is the repo root;
    max_depth 4 means four folders deep under the root.
    """
    cfg = settings or load_settings()
    root = Path(repo_path).resolve()
    paths: list[str] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        parts = rel.parts
        if ".git" in parts:
            continue
        if len(parts) > max_depth:
            continue
        paths.append(rel.as_posix())
        if len(paths) >= cfg.policies.tree_cap_paths:
            break
    return paths
