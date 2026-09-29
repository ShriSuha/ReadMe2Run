from pathlib import Path

from readme2run.configurations.loader import load_settings
from readme2run.sandbox.session import start, stop
from readme2run.sandbox.stream import exec_stream
from readme2run.schemas.plan import RunPlan
from readme2run.workspace.run_dir import create_run
import docker


def test_start_stop_leaves_no_container(tmp_path: Path) -> None:
    settings = load_settings().model_copy(update={"allow_file_urls": True})
    # Use an empty run dir with a tiny repo mount
    run = create_run("file:///tmp/x", runs_root=tmp_path)
    (run.repo / "README.md").write_text("x\n")
    plan = RunPlan(base_image="python:3.11-slim", command_source="readme")
    cid = start(run, plan, settings)
    try:
        assert docker.from_env().containers.get(cid).status in {"created", "running"}
    finally:
        stop(cid)
    ids = {c.id for c in docker.from_env().containers.list(all=True)}
    assert cid not in ids


def test_exec_stream_echo_and_timeout(tmp_path: Path) -> None:
    settings = load_settings()
    run = create_run("file:///tmp/x", runs_root=tmp_path)
    (run.repo / "README.md").write_text("x\n")
    plan = RunPlan(base_image="python:3.11-slim", command_source="readme")
    cid = start(run, plan, settings)
    try:
        lines = []
        code = None
        for kind, value in exec_stream(cid, "echo hello-readme2run", 30):
            if kind == "exit":
                code = value
            else:
                lines.append(value)
        assert code == 0
        assert any("hello-readme2run" in str(x) for x in lines)

        code = None
        for kind, value in exec_stream(cid, "sleep 30", 2):
            if kind == "exit":
                code = value
        assert code == 124
    finally:
        stop(cid)
