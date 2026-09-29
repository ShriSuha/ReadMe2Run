"""Driver agent: run and repair via docker_exec tool."""

from __future__ import annotations

from pathlib import Path

from crewai import Agent, Crew, Process, Task

from readme2run.agents.llm import build_llm
from readme2run.configurations.loader import Settings
from readme2run.schemas.attempt import AttemptLog
from readme2run.schemas.plan import RunPlan
from readme2run.tools.crew_tools import DockerExecTool
from readme2run.tools.docker_exec import docker_exec
from readme2run.tools.git_clone import ToolRejected
from readme2run.workspace.run_dir import RunDir


def _prompt() -> str:
    return (Path(__file__).parent / "prompts" / "driver.md").read_text(encoding="utf-8")


def run_driver_crew(
    *,
    plan: RunPlan,
    container_id: str,
    run_dir: RunDir,
    settings,
    emit,
) -> list[AttemptLog]:
    """Prefer a tool-using Driver crew; fall back to direct docker_exec."""
    try:
        llm = build_llm(settings)
        agent = Agent(
            role="Driver",
            goal="Execute the RunPlan and repair missing dependencies",
            backstory="You run commands in the sandbox with docker_exec.",
            tools=[DockerExecTool()],
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        task = Task(
            description=(
                f"{_prompt()}\n\ncontainer_id={container_id}\n"
                f"plan={plan.model_dump_json()}\n"
                "Call docker_exec for each needed command. "
                "Return a short summary of what you ran."
            ),
            expected_output="Summary of commands run and their results",
            agent=agent,
        )
        Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False).kickoff()
    except Exception as exc:  # noqa: BLE001
        emit("phase", f"driver crew fallback: {exc}")

    # Always also execute deterministically so attempts are recorded even if
    # the model only summarized without calling tools reliably.
    attempts: list[AttemptLog] = []
    for command in plan.setup_commands + plan.run_commands:
        emit("command", command.script)
        try:
            attempt = docker_exec(
                container_id,
                command.script,
                timeout_s=command.timeout_s,
                phase=command.phase,
                on_line=lambda kind, line: emit("log", f"{kind}: {line}"),
            )
        except ToolRejected as exc:
            attempt = AttemptLog(
                command=command.script,
                exit_code=1,
                stdout="",
                stderr=exc.reason,
                duration=0.0,
                phase=command.phase,
            )
        attempts.append(attempt)
        if attempt.exit_code != 0:
            import re

            match = re.search(
                r"ModuleNotFoundError:\s*No module named ['\"]([^'\"]+)['\"]",
                attempt.stderr,
            )
            if match:
                module = match.group(1).split(".")[0]
                fix = f"python -m pip install --no-cache-dir {module}"
                emit("repair", f"install {module}")
                try:
                    install = docker_exec(
                        container_id,
                        fix,
                        timeout_s=settings.sandbox.build_install_timeout,
                        phase="setup",
                    )
                except ToolRejected as exc:
                    attempts.append(
                        AttemptLog(
                            command=fix,
                            exit_code=1,
                            stdout="",
                            stderr=exc.reason,
                            duration=0.0,
                            phase="setup",
                        )
                    )
                    break
                attempts.append(install)
                if install.exit_code == 0:
                    retry = docker_exec(
                        container_id,
                        command.script,
                        timeout_s=command.timeout_s,
                        phase=command.phase,
                    )
                    attempts.append(retry)
            break
    return attempts
