from readme2run.configurations.loader import Settings, load_settings
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import Command, RunPlan


def _timeout(settings: Settings, phase: str) -> int:
    if phase == "setup":
        return settings.sandbox.build_install_timeout
    return settings.sandbox.command_timeout


def _run_commands(facts: RepoFacts, settings: Settings) -> list[Command]:
    return [
        Command(
            script=script,
            timeout_s=_timeout(settings, "run"),
            purpose="run from README",
            phase="run",
        )
        for script in facts.readme.commands
    ]


def python_plan(facts: RepoFacts, settings: Settings | None = None) -> RunPlan:
    """Build a RunPlan for a Python repo from facts."""
    cfg = settings or load_settings()
    setup: list[Command] = []
    manifests = set(facts.manifests)
    if "requirements.txt" in manifests:
        setup.append(
            Command(
                script="python -m pip install --no-cache-dir -r requirements.txt",
                timeout_s=_timeout(cfg, "setup"),
                purpose="install requirements",
                phase="setup",
            )
        )
    elif "pyproject.toml" in manifests:
        # Prefer Poetry when poetry.lock exists; otherwise uv when uv.lock exists.
        if "poetry.lock" in manifests or _mentions_poetry(facts):
            setup.extend(
                [
                    Command(
                        script="python -m pip install --no-cache-dir poetry",
                        timeout_s=_timeout(cfg, "setup"),
                        purpose="install poetry",
                        phase="setup",
                    ),
                    Command(
                        script="poetry install",
                        timeout_s=_timeout(cfg, "setup"),
                        purpose="install with poetry",
                        phase="setup",
                    ),
                ]
            )
        elif "uv.lock" in manifests:
            setup.extend(
                [
                    Command(
                        script="python -m pip install --no-cache-dir uv",
                        timeout_s=_timeout(cfg, "setup"),
                        purpose="install uv",
                        phase="setup",
                    ),
                    Command(
                        script="uv sync",
                        timeout_s=_timeout(cfg, "setup"),
                        purpose="install with uv",
                        phase="setup",
                    ),
                ]
            )
    return RunPlan(
        base_image=cfg.sandbox.images["python"],
        setup_commands=setup,
        run_commands=_run_commands(facts, cfg),
        command_source="readme",
    )


def _mentions_poetry(facts: RepoFacts) -> bool:
    return "poetry" in facts.readme.text.lower()
