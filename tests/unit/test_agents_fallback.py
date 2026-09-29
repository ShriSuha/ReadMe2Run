from readme2run.configurations.loader import load_settings
from readme2run.discovery import inspect_repo
from readme2run.orchestration.repair_loop import default_driver, repair_loop
from readme2run.planning import select_plan
from readme2run.schemas.attempt import AttemptLog
from readme2run.schemas.plan import Command, RunPlan
from readme2run.schemas.repair import RepairAction
from readme2run.schemas.state import RunState
from readme2run.workspace.run_dir import create_run
from pathlib import Path


def test_default_driver_installs_rich() -> None:
    attempt = AttemptLog(
        command="python main.py",
        exit_code=1,
        stdout="",
        stderr="ModuleNotFoundError: No module named 'rich'",
        duration=0.1,
        phase="run",
    )
    plan = RunPlan(base_image="python:3.11-slim", command_source="readme")
    action = default_driver(attempt, plan)
    assert action.kind == "insert_setup_command"
    assert action.command is not None
    assert "rich" in action.command.script


def test_stub_driver_stops_at_max_repairs(tmp_path: Path) -> None:
    settings = load_settings()
    run = create_run("https://github.com/org/repo", runs_root=tmp_path)
    plan = RunPlan(
        base_image="python:3.11-slim",
        run_commands=[
            Command(script="false", timeout_s=10, purpose="fail", phase="run")
        ],
        command_source="readme",
    )
    state = RunState(
        url="https://github.com/org/repo",
        run_directory=str(run.path),
        plan=plan,
        attempts=[
            AttemptLog(
                command="false",
                exit_code=1,
                stdout="",
                stderr="ModuleNotFoundError: No module named 'rich'",
                duration=0.1,
                phase="run",
            )
        ],
    )

    calls = {"n": 0}

    def stub_driver(attempt, current_plan):
        calls["n"] += 1
        return RepairAction(
            kind="insert_setup_command",
            command=Command(
                script="python -m pip install --no-cache-dir rich",
                timeout_s=30,
                purpose="noop",
                phase="setup",
            ),
            reason="always",
        )

    def run_commands(current):
        return [
            AttemptLog(
                command="false",
                exit_code=1,
                stdout="",
                stderr="ModuleNotFoundError: No module named 'rich'",
                duration=0.1,
                phase="run",
            )
        ]

    # Use a fake container path by patching docker_exec inside repair_loop via stub that fails install
    # We only assert the loop caps ask_driver calls via repair_count when installs fail quickly.
    from unittest.mock import patch

    failing = AttemptLog(
        command="python -m pip install --no-cache-dir rich",
        exit_code=1,
        stdout="",
        stderr="fail",
        duration=0.1,
        phase="setup",
    )
    with patch(
        "readme2run.orchestration.repair_loop.docker_exec",
        return_value=failing,
    ):
        repair_loop(
            state=state,
            plan=plan,
            run_dir=run,
            settings=settings,
            container_id="fake",
            run_commands=run_commands,
            ask_driver=stub_driver,
        )
    assert state.repair_count == settings.policies.max_repairs
    assert calls["n"] == settings.policies.max_repairs


def test_architect_fallback_keeps_planner_plan() -> None:
    from unittest.mock import patch

    from readme2run.agents.crew import architect_or_fallback

    facts = inspect_repo(Path("tests/fixtures/hello"))
    settings = load_settings()
    with patch("readme2run.agents.crew.run_architect", return_value=None):
        plan = architect_or_fallback(facts, settings)
    assert plan.run_commands[0].script == "python main.py"
