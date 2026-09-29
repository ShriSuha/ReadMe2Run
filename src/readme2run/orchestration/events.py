"""Append and read run events as JSON lines."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone

from readme2run.schemas.events import RunEvent
from readme2run.workspace.run_dir import RunDir


def publish(run_dir: RunDir, event: RunEvent) -> None:
    """Append one JSON object to events.jsonl."""
    with run_dir.events_path.open("a", encoding="utf-8") as handle:
        handle.write(event.model_dump_json() + "\n")


def iter_events(run_dir: RunDir) -> Iterator[RunEvent]:
    """Yield events from events.jsonl in order."""
    if not run_dir.events_path.is_file():
        return
    for line in run_dir.events_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield RunEvent.model_validate_json(line)


def make_event(run_id: str, kind: str, message: str) -> RunEvent:
    """Build a RunEvent with the current UTC timestamp."""
    return RunEvent(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        kind=kind,  # type: ignore[arg-type]
        message=message,
    )
