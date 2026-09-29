import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from readme2run.configurations.loader import Settings
from readme2run.guardrails.resource_policy import check_repo_size
from readme2run.guardrails.url_policy import url_policy
from readme2run.workspace.run_dir import RunDir


class ToolRejected(Exception):
    """A guardrail refused the action. The tool did not do the work."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class CloneError(Exception):
    """git clone ran and failed."""


class CloneRequest(BaseModel):
    """The typed input for a clone: which URL, which run folder, which settings."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: str
    run_dir: RunDir
    settings: Settings


class CloneResult(BaseModel):
    """The typed output of a clone: the checkout directory."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path


class GitCloneTool:
    """Clone one repository into RunDir.repo.

    Order: url_policy, then git clone --depth 1, then the repo size check.
    A rejected URL never calls git. run_git is replaceable in tests.
    """

    def __init__(self, run_git: Callable[[list[str]], None] | None = None) -> None:
        self._run_git = run_git or _run_git

    def run(self, request: CloneRequest) -> CloneResult:
        """Clone request.url into the run folder and return that path."""
        decision = url_policy(request.url, request.settings)
        if not decision.allowed:
            raise ToolRejected(decision.reason)

        destination = request.run_dir.repo
        # git clone creates the destination. An empty folder already there blocks it.
        if destination.exists() and not any(destination.iterdir()):
            destination.rmdir()
        self._run_git(["git", "clone", "--depth", "1", request.url, str(destination)])

        size_decision = check_repo_size(_directory_size(destination), request.settings)
        if not size_decision.allowed:
            shutil.rmtree(destination)
            destination.mkdir()
            raise ToolRejected(size_decision.reason)
        return CloneResult(path=destination)


def _run_git(args: list[str]) -> None:
    """Run one git command. Raise CloneError when git exits non-zero."""
    completed = subprocess.run(args, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise CloneError(detail or f"git failed with exit code {completed.returncode}")


def _directory_size(path: Path) -> int:
    """Total size in bytes of every file under path, including .git."""
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
