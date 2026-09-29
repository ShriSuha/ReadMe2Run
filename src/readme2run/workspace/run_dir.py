import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict

from readme2run.configurations.loader import load_settings


class RunDir(BaseModel):
    """The folder for one run. Later steps receive this instead of inventing a path.

    path is the run folder. repo is where the clone goes. logs holds captured
    output. events_path is the events.jsonl file for this run.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    repo: Path
    logs: Path
    events_path: Path


def create_run(url: str, runs_root: Path | None = None) -> RunDir:
    """Create the folder tree for one run and return it.

    The folder name is a timestamp plus a short name from the URL, for example
    20260929T120000-repo. Pass runs_root in a test so the folders stay in a
    temporary directory. When it is omitted, the runs directory from settings
    is used.
    """
    root = Path(runs_root) if runs_root is not None else _default_runs_root()
    root.mkdir(parents=True, exist_ok=True)
    run_path = _unique_directory(root, f"{_timestamp()}-{_slug(url)}")
    repo = run_path / "repo"
    logs = run_path / "logs"
    events_path = run_path / "events.jsonl"
    repo.mkdir(parents=True)
    logs.mkdir()
    events_path.write_text("")
    return RunDir(path=run_path, repo=repo, logs=logs, events_path=events_path)


def cleanup(run_dir: RunDir) -> None:
    """Delete the run folder, including repo, logs, and events.jsonl.

    Refuses to delete the filesystem root or the home directory. If the
    folder is already gone, this does nothing.
    """
    root = run_dir.path.resolve()
    if root == Path("/").resolve() or root == Path.home().resolve():
        raise ValueError(f"refusing to delete {root}")
    if root.exists():
        shutil.rmtree(root)


def _default_runs_root() -> Path:
    """The runs directory from app settings, with ~ expanded."""
    return Path(load_settings().app.runs_dir).expanduser()


def _timestamp() -> str:
    """UTC time safe to use in a folder name, such as 20260929T120000."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


def _slug(url: str) -> str:
    """A short filesystem-safe name taken from the last part of the URL.

    https://github.com/org/repo.git becomes repo. A URL with no usable
    name becomes the word repo.
    """
    name = urlparse(url).path.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[: -len(".git")]
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-._")
    return cleaned.lower() or "repo"


def _unique_directory(parent: Path, name: str) -> Path:
    """Return a new directory path. Add -2, -3, ... if the name is taken."""
    candidate = parent / name
    number = 2
    while candidate.exists():
        candidate = parent / f"{name}-{number}"
        number += 1
    return candidate
