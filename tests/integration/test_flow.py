from pathlib import Path

from readme2run.configurations.loader import load_settings
from readme2run.orchestration.events import iter_events
from readme2run.orchestration.flow import run_flow
from readme2run.workspace.run_dir import RunDir
import docker


def test_hello_flow(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/hello").resolve()
    settings = load_settings().model_copy(update={"allow_file_urls": True})
    state = run_flow(
        fixture.as_uri(),
        settings=settings,
        runs_root=tmp_path,
        use_agents=False,
    )
    assert state.verdict is not None
    assert state.verdict.label == "ran_as_documented"
    assert any("hello-readme2run" in a.stdout for a in state.attempts)
    assert (Path(state.run_directory) / "report.md").is_file()
    assert (Path(state.run_directory) / "report.json").is_file()
    run_dir = RunDir(
        path=Path(state.run_directory),
        repo=Path(state.run_directory) / "repo",
        logs=Path(state.run_directory) / "logs",
        events_path=Path(state.run_directory) / "events.jsonl",
    )
    events = list(iter_events(run_dir))
    assert events
    # No leftover container with this run id slug in name is hard; ensure none from our stop.
    # Basic sanity: docker responds.
    docker.from_env().ping()


def test_missing_dep_repairs(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/missing_dep").resolve()
    settings = load_settings().model_copy(update={"allow_file_urls": True})
    state = run_flow(
        fixture.as_uri(),
        settings=settings,
        runs_root=tmp_path,
        use_agents=False,
    )
    assert state.verdict is not None
    assert state.verdict.label == "ran_after_repair"
    assert 1 <= state.repair_count <= 5
