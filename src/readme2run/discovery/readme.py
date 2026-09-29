import re
from pathlib import Path

from readme2run.configurations.loader import Settings, load_settings
from readme2run.schemas.facts import ReadmeFacts

_FENCE = re.compile(
    r"```(?:bash|shell|sh)\s*\n(.*?)```",
    re.IGNORECASE | re.DOTALL,
)


def read_readme(repo_path: Path, settings: Settings | None = None) -> ReadmeFacts:
    """Read README.md up to the character cap and collect bash/shell fences."""
    cfg = settings or load_settings()
    path = Path(repo_path) / "README.md"
    if not path.is_file():
        for name in ("readme.md", "Readme.md"):
            alt = Path(repo_path) / name
            if alt.is_file():
                path = alt
                break
        else:
            return ReadmeFacts()
    text = path.read_text(encoding="utf-8", errors="replace")
    cap = cfg.policies.readme_cap_characters
    if len(text) > cap:
        text = text[:cap]
    commands: list[str] = []
    for block in _FENCE.findall(text):
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            commands.append(stripped)
    return ReadmeFacts(text=text, commands=commands)
