from pathlib import Path

import pytest

from readme2run.discovery import inspect_repo
from readme2run.planning import InsufficientReadmeError, select_plan
from readme2run.planning.go_plan import go_plan
from readme2run.planning.node_plan import node_plan
from readme2run.planning.python_plan import python_plan
from readme2run.schemas.facts import ReadmeFacts, RepoFacts


def test_hello_python_plan() -> None:
    facts = inspect_repo(Path("tests/fixtures/hello"))
    plan = python_plan(facts)
    assert plan.setup_commands[0].script.endswith("requirements.txt")
    assert plan.run_commands[0].script == "python main.py"
    assert plan.command_source == "readme"


def test_node_plan_uses_npm_ci() -> None:
    facts = inspect_repo(Path("tests/fixtures/node_app"))
    plan = node_plan(facts)
    assert plan.setup_commands[0].script == "npm ci"
    assert plan.run_commands[0].script == "node index.js"


def test_go_base_image() -> None:
    facts = RepoFacts(
        readme=ReadmeFacts(commands=["go run ."]),
        manifests=["go.mod"],
        languages=["go"],
    )
    plan = go_plan(facts)
    assert plan.base_image == "golang:1.22"


def test_select_plan_dockerfile_and_ci_and_error() -> None:
    docker_facts = inspect_repo(Path("tests/fixtures/full_stack"))
    plan = select_plan(docker_facts)
    assert plan.dockerfile_path == "Dockerfile"

    ci_facts = inspect_repo(Path("tests/fixtures/ci_only"))
    ci_plan = select_plan(ci_facts)
    assert ci_plan.command_source == "ci"
    assert ci_plan.run_commands[0].script == "python main.py"

    with pytest.raises(InsufficientReadmeError):
        select_plan(RepoFacts(languages=["python"]))
