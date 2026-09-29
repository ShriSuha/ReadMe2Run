from readme2run.configurations.loader import Settings, load_settings
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import Command, RunPlan


def go_plan(facts: RepoFacts, settings: Settings | None = None) -> RunPlan:
    """Build a RunPlan for a Go repo from facts."""
    cfg = settings or load_settings()
    setup = [
        Command(
            script="go mod download",
            timeout_s=cfg.sandbox.build_install_timeout,
            purpose="download go modules",
            phase="setup",
        )
    ]
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
        base_image=cfg.sandbox.images["go"],
        setup_commands=setup,
        run_commands=runs,
        command_source="readme",
    )
