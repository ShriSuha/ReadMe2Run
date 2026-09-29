from readme2run.configurations.loader import Settings, load_settings
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import Command, RunPlan


def node_plan(facts: RepoFacts, settings: Settings | None = None) -> RunPlan:
    """Build a RunPlan for a Node repo from facts."""
    cfg = settings or load_settings()
    manifests = set(facts.manifests)
    if "package-lock.json" in manifests:
        script = "npm ci"
    elif "pnpm-lock.yaml" in manifests:
        script = "pnpm install"
    elif "yarn.lock" in manifests:
        script = "yarn install"
    else:
        script = "npm install"
    setup = [
        Command(
            script=script,
            timeout_s=cfg.sandbox.build_install_timeout,
            purpose="install node dependencies",
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
        base_image=cfg.sandbox.images["node"],
        setup_commands=setup,
        run_commands=runs,
        command_source="readme",
    )
