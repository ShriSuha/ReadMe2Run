"""Inspector agent: explore the repo with tools and return RepoFacts."""

from __future__ import annotations

from pathlib import Path

from crewai import Agent, Crew, Process, Task

from readme2run.agents.llm import build_llm
from readme2run.configurations.loader import Settings
from readme2run.discovery import inspect_repo
from readme2run.guardrails.prompt_data import wrap_untrusted
from readme2run.schemas.facts import RepoFacts
from readme2run.tools.crew_tools import DirectoryTreeTool, ReadFileTool


def _prompt() -> str:
    return (Path(__file__).parent / "prompts" / "inspector.md").read_text(encoding="utf-8")


def run_inspector(repo_path: Path, settings: Settings) -> RepoFacts:
    """Run the Inspector crew. Falls back to inspect_repo on failure."""
    try:
        llm = build_llm(settings)
        agent = Agent(
            role="Inspector",
            goal="Fill RepoFacts for the checkout using tools",
            backstory="You carefully list files and read documentation.",
            tools=[DirectoryTreeTool(), ReadFileTool()],
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        task = Task(
            description=(
                f"{_prompt()}\n\nRepo path: {repo_path}\n"
                f"{wrap_untrusted(f'repository at {repo_path}')}"
            ),
            expected_output="A RepoFacts object",
            agent=agent,
            output_pydantic=RepoFacts,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
        result = crew.kickoff()
        if isinstance(result.pydantic, RepoFacts):
            return result.pydantic
    except Exception:
        pass
    return inspect_repo(repo_path, settings)
