"""CrewAI crew wiring for ReadMe2Run.

Beginner layout (like a typical CrewAI tutorial):
- config/agents.yaml  — who the agents are
- config/tasks.yaml   — what each task asks for
- crew.py             — wires agents, tasks, tools, and the LLM

Orchestration still decides *when* each crew runs (see orchestration/flow.py).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from readme2run.agents.llm import build_llm
from readme2run.configurations.loader import Settings, load_settings
from readme2run.discovery import inspect_repo
from readme2run.guardrails.prompt_data import wrap_untrusted
from readme2run.planning import select_plan
from readme2run.schemas.attempt import AttemptLog
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import RunPlan
from readme2run.schemas.state import RunState
from readme2run.tools.crew_tools import DirectoryTreeTool, DockerExecTool, ReadFileTool
from readme2run.tools.docker_exec import docker_exec
from readme2run.tools.git_clone import ToolRejected
from readme2run.workspace.run_dir import RunDir

_CONFIG_DIR = Path(__file__).parent / "config"


@CrewBase
class ReadMe2RunCrew:
    """One place that connects YAML names to Python agents, tasks, and tools."""

    agents_config = str(_CONFIG_DIR / "agents.yaml")
    tasks_config = str(_CONFIG_DIR / "tasks.yaml")

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.llm = build_llm(self.settings)

    # --- agents (names must match agents.yaml) ---

    @agent
    def inspector(self) -> Agent:
        return Agent(
            config=self.agents_config["inspector"],  # type: ignore[index]
            tools=[DirectoryTreeTool(), ReadFileTool()],
            llm=self.llm,
        )

    @agent
    def architect(self) -> Agent:
        return Agent(
            config=self.agents_config["architect"],  # type: ignore[index]
            tools=[DirectoryTreeTool(), ReadFileTool()],
            llm=self.llm,
        )

    @agent
    def driver(self) -> Agent:
        return Agent(
            config=self.agents_config["driver"],  # type: ignore[index]
            tools=[DockerExecTool()],
            llm=self.llm,
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["analyst"],  # type: ignore[index]
            llm=self.llm,
        )

    # --- tasks (names must match tasks.yaml) ---

    @task
    def inspect_repo(self) -> Task:
        return Task(
            config=self.tasks_config["inspect_repo"],  # type: ignore[index]
            output_pydantic=RepoFacts,
        )

    @task
    def plan_run(self) -> Task:
        return Task(
            config=self.tasks_config["plan_run"],  # type: ignore[index]
            output_pydantic=RunPlan,
        )

    @task
    def drive_run(self) -> Task:
        return Task(config=self.tasks_config["drive_run"])  # type: ignore[index]

    @task
    def write_evidence(self) -> Task:
        return Task(config=self.tasks_config["write_evidence"])  # type: ignore[index]

    # --- crew builders: one small crew per phase ---

    @crew
    def crew(self) -> Crew:
        """Default crew (all agents). Prefer the phase helpers below."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )

    def inspector_crew(self) -> Crew:
        return Crew(
            agents=[self.inspector()],
            tasks=[self.inspect_repo()],
            process=Process.sequential,
            verbose=False,
        )

    def architect_crew(self) -> Crew:
        return Crew(
            agents=[self.architect()],
            tasks=[self.plan_run()],
            process=Process.sequential,
            verbose=False,
        )

    def driver_crew(self) -> Crew:
        return Crew(
            agents=[self.driver()],
            tasks=[self.drive_run()],
            process=Process.sequential,
            verbose=False,
        )

    def analyst_crew(self) -> Crew:
        return Crew(
            agents=[self.analyst()],
            tasks=[self.write_evidence()],
            process=Process.sequential,
            verbose=False,
        )


# --- public helpers used by orchestration/flow.py ---


def run_inspector(repo_path: Path, settings: Settings) -> RepoFacts:
    """Run the Inspector crew. Falls back to inspect_repo on failure."""
    try:
        result = ReadMe2RunCrew(settings).inspector_crew().kickoff(
            inputs={
                "repo_path": str(repo_path),
                "untrusted_block": wrap_untrusted(f"repository at {repo_path}"),
            }
        )
        if isinstance(result.pydantic, RepoFacts):
            return result.pydantic
    except Exception:
        pass
    return inspect_repo(repo_path, settings)


def run_architect(facts: RepoFacts, settings: Settings) -> RunPlan | None:
    """Ask the Architect for a RunPlan. Return None on failure."""
    try:
        result = ReadMe2RunCrew(settings).architect_crew().kickoff(
            inputs={"untrusted_block": wrap_untrusted(facts.model_dump_json())}
        )
        if isinstance(result.pydantic, RunPlan):
            return result.pydantic
    except Exception:
        return None
    return None


def architect_or_fallback(facts: RepoFacts, settings: Settings) -> RunPlan:
    plan = run_architect(facts, settings)
    if plan is not None and plan.run_commands:
        return plan
    return select_plan(facts, settings)


def run_driver_crew(
    *,
    plan: RunPlan,
    container_id: str,
    run_dir: RunDir,
    settings: Settings,
    emit: Any,
) -> list[AttemptLog]:
    """Prefer a tool-using Driver crew; always record deterministic attempts too."""
    try:
        ReadMe2RunCrew(settings).driver_crew().kickoff(
            inputs={
                "container_id": container_id,
                "plan_json": plan.model_dump_json(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        emit("phase", f"driver crew fallback: {exc}")

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


def write_evidence(state: RunState) -> str:
    """Ask the Analyst for evidence text. Fall back to the rule-based evidence."""
    label = state.verdict.label if state.verdict else "failed"
    fallback = state.verdict.evidence if state.verdict else ""
    log_tail = "\n".join(
        f"{a.command} -> {a.exit_code}\n{a.stdout[-200:]}\n{a.stderr[-200:]}"
        for a in state.attempts[-3:]
    )
    try:
        result = ReadMe2RunCrew().analyst_crew().kickoff(
            inputs={"label": label, "log_tail": log_tail}
        )
        text = str(result.raw or result).strip()
        return text or fallback
    except Exception:
        return fallback
