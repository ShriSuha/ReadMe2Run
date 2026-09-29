from readme2run.configurations.loader import Settings, load_settings
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import Command, RunPlan


def rust_plan(facts: RepoFacts, settings: Settings | None = None) -> RunPlan:
    """Build a RunPlan for a Rust repo from facts."""
    cfg = settings or load_settings()
    setup = [
        Command(
            script=cmd,
            timeout_s=cfg.sandbox.build_install_timeout,
            purpose="setup from README",
            phase="setup",
        )
        for cmd in facts.readme.commands
        if cmd.startswith("cargo install") or "apt" in cmd
    ]
    runs = [
        Command(
            script=cmd,
            timeout_s=cfg.sandbox.command_timeout,
            purpose="run from README",
            phase="run",
        )
        for cmd in facts.readme.commands
        if cmd not in {c.script for c in setup}
    ]
    return RunPlan(
        base_image=cfg.sandbox.images["rust"],
        setup_commands=setup,
        run_commands=runs,
        command_source="readme",
    )
