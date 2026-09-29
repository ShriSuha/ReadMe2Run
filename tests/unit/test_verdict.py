from pathlib import Path

from readme2run.reporting.verdict import decide_verdict
from readme2run.schemas.attempt import AttemptLog
from readme2run.schemas.facts import ReadmeFacts, RepoFacts
from readme2run.schemas.plan import Command, RunPlan


def _attempt(code: int) -> AttemptLog:
    return AttemptLog(
        command="python main.py",
        exit_code=code,
        stdout="hello-readme2run",
        stderr="",
        duration=0.1,
        phase="run",
    )


def test_verdict_labels() -> None:
    plan = RunPlan(
        base_image="python:3.11-slim",
        run_commands=[
            Command(script="python main.py", timeout_s=30, purpose="run", phase="run")
        ],
        command_source="readme",
    )
    hello = decide_verdict(RepoFacts(), plan, [_attempt(0)], repair_count=0)
    assert hello.label == "ran_as_documented"

    repaired = decide_verdict(RepoFacts(), plan, [_attempt(0)], repair_count=1)
    assert repaired.label == "ran_after_repair"

    empty = decide_verdict(RepoFacts(), RunPlan(command_source="readme"), [], 0)
    assert empty.label == "readme_insufficient"
