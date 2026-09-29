"""List expected artifacts that already exist under the checkout."""

from pathlib import Path

from readme2run.configurations.loader import Settings, load_settings
from readme2run.guardrails.resource_policy import check_tree_length
from readme2run.tools.git_clone import ToolRejected


def artifact_list(
    repo_path: Path | str,
    expected: list[str],
    settings: Settings | None = None,
) -> list[str]:
    """Return which of the expected relative paths exist on disk."""
    cfg = settings or load_settings()
    root = Path(repo_path)
    found = [name for name in expected if (root / name).exists()]
    decision = check_tree_length(len(found), cfg)
    if not decision.allowed:
        raise ToolRejected(decision.reason)
    return found
