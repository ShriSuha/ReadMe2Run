from typing import Literal

from pydantic import BaseModel, Field


class ReadmeFacts(BaseModel):
    """The README text and the shell commands copied out of its fenced blocks."""

    text: str = ""
    commands: list[str] = Field(default_factory=list)


class RepoFacts(BaseModel):
    """What discovery learned about a repo before any model sees it.

    Planning reads this object and turns it into a RunPlan. Groups pass
    this object around instead of a loose dictionary.
    """

    readme: ReadmeFacts = Field(default_factory=ReadmeFacts)
    # Relative file paths, with .git left out.
    tree: list[str] = Field(default_factory=list)
    # Manifest and lockfile paths, such as requirements.txt or package.json.
    manifests: list[str] = Field(default_factory=list)
    dockerfile_path: str | None = None
    makefile_targets: list[str] = Field(default_factory=list)
    ci_commands: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    # Why a run may be unable to finish: a GPU, a secret, or a notebook.
    blockers: list[Literal["gpu", "secret", "notebook"]] = Field(default_factory=list)
