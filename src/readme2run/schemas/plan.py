from typing import Literal

from pydantic import BaseModel, Field


class Command(BaseModel):
    """One shell command the sandbox will run."""

    script: str
    timeout_s: int
    # Why this command is in the plan, for example "install dependencies".
    purpose: str
    # "setup" installs things. "run" executes the project.
    phase: str


class RunPlan(BaseModel):
    """How to run one repo. Every language uses this same shape.

    Built from RepoFacts. Each command that actually runs becomes an AttemptLog.
    Use base_image for a language image from settings, or dockerfile_path
    when the repo brings its own Dockerfile.
    """

    base_image: str | None = None
    dockerfile_path: str | None = None
    # Directory inside the container where the repo is mounted.
    workdir: str = "/work"
    # Environment variables to set inside the container.
    env: dict[str, str] = Field(default_factory=dict)
    setup_commands: list[Command] = Field(default_factory=list)
    run_commands: list[Command] = Field(default_factory=list)
    # Text that should appear in the output when the run worked.
    success_signals: list[str] = Field(default_factory=list)
    # Files the run is expected to create, such as a report or a plot.
    expected_artifacts: list[str] = Field(default_factory=list)
    # "readme" when the commands came from the README, "ci" when they came from CI.
    command_source: Literal["readme", "ci"]
