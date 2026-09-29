from datetime import datetime, timezone

from pydantic import BaseModel

from readme2run.schemas.attempt import AttemptLog
from readme2run.schemas.events import RunEvent
from readme2run.schemas.facts import ReadmeFacts, RepoFacts
from readme2run.schemas.plan import Command, RunPlan
from readme2run.schemas.repair import RepairAction
from readme2run.schemas.state import RunState
from readme2run.schemas.verdict import Verdict


def _round_trip(model: BaseModel) -> None:
    """Save a model as JSON and load it back into an equal object."""
    restored = type(model).model_validate_json(model.model_dump_json())
    assert restored == model


def test_each_model_round_trips_through_json() -> None:
    command = Command(
        script="python main.py",
        timeout_s=300,
        purpose="run the project",
        phase="run",
    )
    attempt = AttemptLog(
        command="python main.py",
        exit_code=0,
        stdout="hello-readme2run",
        stderr="",
        duration=1.5,
        phase="run",
    )
    facts = RepoFacts(
        readme=ReadmeFacts(text="# Hello", commands=["python main.py"]),
        tree=["main.py", "requirements.txt"],
        manifests=["requirements.txt"],
        dockerfile_path="Dockerfile",
        makefile_targets=["test"],
        ci_commands=["pytest"],
        languages=["python"],
        blockers=["secret"],
    )
    plan = RunPlan(
        base_image="python:3.11-slim",
        workdir="/work",
        env={"COLOR": "1"},
        setup_commands=[
            Command(
                script="python -m pip install -r requirements.txt",
                timeout_s=900,
                purpose="install dependencies",
                phase="setup",
            )
        ],
        run_commands=[command],
        success_signals=["hello-readme2run"],
        expected_artifacts=["output.txt"],
        command_source="readme",
    )
    repair = RepairAction(
        kind="insert_setup_command",
        command=Command(
            script="python -m pip install rich",
            timeout_s=300,
            purpose="install a missing module",
            phase="setup",
        ),
        reason="main.py imports rich",
    )
    verdict = Verdict(
        label="ran_as_documented",
        evidence="The documented command exited 0.",
        attempts=[attempt],
    )
    event = RunEvent(
        run_id="20260929-hello",
        timestamp=datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc),
        kind="verdict",
        message="ran_as_documented",
    )
    state = RunState(
        url="https://github.com/org/repo",
        run_directory="/tmp/readme2run/20260929-hello",
        facts=facts,
        plan=plan,
        attempts=[attempt],
        repair_count=0,
        verdict=verdict,
    )

    for model in (facts.readme, facts, command, plan, attempt, repair, verdict, event, state):
        _round_trip(model)
