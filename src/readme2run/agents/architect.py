"""Architect agent: produce a RunPlan with optional tool use."""

from __future__ import annotations

from pathlib import Path

from crewai import Agent, Crew, Process, Task

from readme2run.agents.llm import build_llm
from readme2run.configurations.loader import Settings
from readme2run.guardrails.prompt_data import wrap_untrusted
from readme2run.planning import select_plan
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import RunPlan
from readme2run.tools.crew_tools import DirectoryTreeTool, ReadFileTool


def _prompt() -> str:
    return (Path(__file__).parent / "prompts" / "architect.md").read_text(encoding="utf-8")


def run_architect(facts: RepoFacts, settings: Settings) -> RunPlan | None:
    """Ask the Architect for a RunPlan. Return None on failure."""
    try:
        llm = build_llm(settings)
        agent = Agent(
            role="Architect",
            goal="Produce a safe RunPlan from repository facts",
            backstory="You turn documentation into setup and run commands.",
            tools=[DirectoryTreeTool(), ReadFileTool()],
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        task = Task(
            description=(
                f"{_prompt()}\n\nFacts JSON:\n{wrap_untrusted(facts.model_dump_json())}"
            ),
            expected_output="A RunPlan object",
            agent=agent,
            output_pydantic=RunPlan,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
        result = crew.kickoff()
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
