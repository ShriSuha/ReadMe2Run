"""Write report.md and report.json for a finished run."""

from __future__ import annotations

from pathlib import Path

from readme2run.schemas.state import RunState


def write_json_report(run_directory: Path | str, state: RunState) -> Path:
    path = Path(run_directory) / "report.json"
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return path


def write_markdown_report(run_directory: Path | str, state: RunState) -> Path:
    path = Path(run_directory) / "report.md"
    label = state.verdict.label if state.verdict else "unknown"
    lines = [
        f"# ReadMe2Run report",
        "",
        f"- URL: `{state.url}`",
        f"- Verdict: **{label}**",
        f"- Repairs: {state.repair_count}",
        "",
    ]
    if state.verdict:
        lines.extend(["## Evidence", "", state.verdict.evidence, ""])
    if state.plan:
        lines.extend(["## Plan", ""])
        if state.plan.base_image:
            lines.append(f"- Base image: `{state.plan.base_image}`")
        if state.plan.dockerfile_path:
            lines.append(f"- Dockerfile: `{state.plan.dockerfile_path}`")
        lines.append(f"- Command source: `{state.plan.command_source}`")
        lines.append("")
        lines.append("### Commands")
        for cmd in state.plan.setup_commands + state.plan.run_commands:
            lines.append(f"- ({cmd.phase}) `{cmd.script}`")
        lines.append("")
    lines.extend(["## Attempts", ""])
    for attempt in state.attempts:
        lines.append(f"### `{attempt.command}`")
        lines.append(f"- exit: {attempt.exit_code}")
        lines.append(f"- duration: {attempt.duration:.2f}s")
        if attempt.stdout:
            lines.append("```")
            lines.append("\n".join(attempt.stdout.splitlines()[-20:]))
            lines.append("```")
        if attempt.stderr:
            lines.append("stderr:")
            lines.append("```")
            lines.append("\n".join(attempt.stderr.splitlines()[-20:]))
            lines.append("```")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
