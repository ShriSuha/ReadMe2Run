from readme2run.configurations.loader import Settings, load_settings
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import Command, RunPlan


def docker_plan(facts: RepoFacts, settings: Settings | None = None) -> RunPlan:
    """Plan that uses the repo Dockerfile and README run commands."""
    cfg = settings or load_settings()
    if not facts.dockerfile_path:
        raise ValueError("docker_plan needs a dockerfile_path on facts")
    runs = [
        Command(
            script=cmd,
            timeout_s=cfg.sandbox.command_timeout,
            purpose="run from README",
            phase="run",
        )
        for cmd in facts.readme.commands
    ]
    return RunPlan(
        dockerfile_path=facts.dockerfile_path,
        setup_commands=[],
        run_commands=runs,
        command_source="readme",
    )


def from_ci(facts: RepoFacts, settings: Settings | None = None) -> RunPlan:
    """When the README has no fences, use the first CI run step."""
    cfg = settings or load_settings()
    if not facts.ci_commands:
        raise ValueError("from_ci needs ci_commands on facts")
    script = facts.ci_commands[0]
    return RunPlan(
        base_image=cfg.sandbox.images.get("python", "python:3.11-slim"),
        setup_commands=[],
        run_commands=[
            Command(
                script=script,
                timeout_s=cfg.sandbox.command_timeout,
                purpose="run from CI",
                phase="run",
            )
        ],
        command_source="ci",
    )
