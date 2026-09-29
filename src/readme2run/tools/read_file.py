"""Read one file from the checkout, capped by the resource policy."""

from pathlib import Path

from readme2run.configurations.loader import Settings, load_settings
from readme2run.guardrails.resource_policy import check_readme_length
from readme2run.tools.git_clone import ToolRejected


def read_file(
    repo_path: Path | str,
    relative_path: str,
    settings: Settings | None = None,
) -> str:
    """Read a file under the repo. Rejects paths that escape the checkout."""
    cfg = settings or load_settings()
    root = Path(repo_path).resolve()
    target = (root / relative_path).resolve()
    if not str(target).startswith(str(root)):
        raise ToolRejected("path escapes the repository checkout")
    if not target.is_file():
        raise ToolRejected(f"file not found: {relative_path}")
    text = target.read_text(encoding="utf-8", errors="replace")
    decision = check_readme_length(len(text), cfg)
    if not decision.allowed:
        text = text[: cfg.policies.readme_cap_characters]
    return text
