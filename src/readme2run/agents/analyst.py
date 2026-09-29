"""Analyst agent: write the evidence paragraph for a verdict."""

from __future__ import annotations

from pathlib import Path

from crewai import Agent, Crew, Process, Task

from readme2run.agents.llm import build_llm
from readme2run.schemas.state import RunState


def _prompt() -> str:
    return (Path(__file__).parent / "prompts" / "analyst.md").read_text(encoding="utf-8")


def write_evidence(state: RunState) -> str:
    """Ask the Analyst for evidence text. Fall back to the rule-based evidence."""
    label = state.verdict.label if state.verdict else "failed"
    fallback = state.verdict.evidence if state.verdict else ""
    log_tail = "\n".join(
        f"{a.command} -> {a.exit_code}\n{a.stdout[-200:]}\n{a.stderr[-200:]}"
        for a in state.attempts[-3:]
    )
    try:
        llm = build_llm()
        agent = Agent(
            role="Analyst",
            goal="Explain the verdict in plain language",
            backstory="You write short evidence for run reports.",
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        task = Task(
            description=(
                f"{_prompt()}\n\nlabel={label}\nlog_tail:\n{log_tail}\n"
                "Return only the evidence paragraph."
            ),
            expected_output="A short evidence paragraph",
            agent=agent,
        )
        result = Crew(
            agents=[agent], tasks=[task], process=Process.sequential, verbose=False
        ).kickoff()
        text = str(result.raw or result).strip()
        return text or fallback
    except Exception:
        return fallback
