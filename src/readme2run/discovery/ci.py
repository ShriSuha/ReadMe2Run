from pathlib import Path

import yaml


def find_ci_commands(repo_path: Path) -> list[str]:
    """Collect run: steps from .github/workflows/*.yml files."""
    workflows = Path(repo_path) / ".github" / "workflows"
    if not workflows.is_dir():
        return []
    commands: list[str] = []
    for path in sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        jobs = data.get("jobs") or {}
        if not isinstance(jobs, dict):
            continue
        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if isinstance(step, dict) and isinstance(step.get("run"), str):
                    for line in step["run"].splitlines():
                        stripped = line.strip()
                        if stripped and not stripped.startswith("#"):
                            commands.append(stripped)
    return commands
