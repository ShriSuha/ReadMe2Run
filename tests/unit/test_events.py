from datetime import datetime, timezone
from pathlib import Path

from readme2run.orchestration.events import iter_events, make_event, publish
from readme2run.workspace.run_dir import create_run


def test_publish_and_iter_events(tmp_path: Path) -> None:
    run = create_run("https://github.com/org/repo", runs_root=tmp_path)
    first = make_event(run.path.name, "phase", "clone")
    second = make_event(run.path.name, "log", "hello")
    # Stable timestamps for equality checks are not required; order is.
    publish(run, first)
    publish(run, second)
    events = list(iter_events(run))
    assert [e.message for e in events] == ["clone", "hello"]
    assert events[0].kind == "phase"
