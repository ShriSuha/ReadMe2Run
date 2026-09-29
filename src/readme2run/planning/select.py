from readme2run.configurations.loader import Settings, load_settings
from readme2run.planning.docker_plan import docker_plan, from_ci
from readme2run.planning.go_plan import go_plan
from readme2run.planning.node_plan import node_plan
from readme2run.planning.python_plan import python_plan
from readme2run.planning.rust_plan import rust_plan
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import RunPlan


class InsufficientReadmeError(Exception):
    """No run command could be found in the README or CI."""


def select_plan(facts: RepoFacts, settings: Settings | None = None) -> RunPlan:
    """Pick a RunPlan. Dockerfile wins; then language; then CI; else error."""
    cfg = settings or load_settings()
    if facts.dockerfile_path:
        plan = docker_plan(facts, cfg)
        if plan.run_commands:
            return plan
        if facts.ci_commands:
            ci = from_ci(facts, cfg)
            return ci.model_copy(update={"dockerfile_path": facts.dockerfile_path})
        raise InsufficientReadmeError("Dockerfile present but no run command found")

    languages = facts.languages
    if "python" in languages:
        plan = python_plan(facts, cfg)
    elif "node" in languages:
        plan = node_plan(facts, cfg)
    elif "go" in languages:
        plan = go_plan(facts, cfg)
    elif "rust" in languages:
        plan = rust_plan(facts, cfg)
    else:
        plan = None

    if plan is not None and plan.run_commands:
        return plan
    if facts.ci_commands:
        return from_ci(facts, cfg)
    raise InsufficientReadmeError("no run command in README or CI")
