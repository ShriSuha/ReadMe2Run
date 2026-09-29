"""List the repo tree for agents and orchestration, capped by policy."""

from pathlib import Path

from readme2run.configurations.loader import Settings, load_settings
from readme2run.discovery.tree import list_tree
from readme2run.guardrails.resource_policy import check_tree_length
from readme2run.tools.git_clone import ToolRejected


def directory_tree(repo_path: Path | str, settings: Settings | None = None) -> list[str]:
    """Return relative paths under the checkout, honoring the tree cap."""
    cfg = settings or load_settings()
    paths = list_tree(Path(repo_path), cfg)
    decision = check_tree_length(len(paths), cfg)
    if not decision.allowed:
        raise ToolRejected(decision.reason)
    return paths
