import re
from pathlib import Path
from typing import Literal

from readme2run.schemas.facts import ReadmeFacts

Blocker = Literal["gpu", "secret", "notebook"]

_GPU = re.compile(r"\b(cuda|gpu|nvidia)\b", re.IGNORECASE)
_SECRET = re.compile(
    r"\b(OPENAI_API_KEY|API_KEY|GITHUB_TOKEN|SECRET|set .*(KEY|TOKEN)|export .*(KEY|TOKEN))\b",
    re.IGNORECASE,
)


def find_blockers(readme: ReadmeFacts, tree: list[str]) -> list[Blocker]:
    """Mark gpu, secret, or notebook when the README or tree shows them."""
    found: list[Blocker] = []
    text = readme.text
    if _GPU.search(text) or any("cuda" in p.lower() for p in tree):
        found.append("gpu")
    if _SECRET.search(text) or any(p.endswith(".env") or p == ".env" for p in tree):
        found.append("secret")
    if any(p.endswith(".ipynb") for p in tree) or "notebook" in text.lower():
        found.append("notebook")
    return found
