"""End-to-end run flow. Agents are optional; deterministic fallbacks always work."""

from __future__ import annotations

from pathlib import Path

from readme2run.configurations.loader import Settings, load_settings
from readme2run.discovery import inspect_repo
from readme2run.orchestration.events import make_event, publish
from readme2run.orchestration.repair_loop import default_driver, repair_loop
from readme2run.planning import InsufficientReadmeError, select_plan
from readme2run.reporting.markdown_report import write_json_report, write_markdown_report
from readme2run.reporting.verdict import decide_verdict
from readme2run.sandbox.session import start, stop
from readme2run.schemas.attempt import AttemptLog
from readme2run.schemas.plan import RunPlan
from readme2run.schemas.state import RunState
from readme2run.tools.docker_exec import docker_exec
from readme2run.tools.git_clone import CloneRequest, GitCloneTool, ToolRejected
from readme2run.workspace.run_dir import RunDir, create_run


def run_flow(
    url: str,
    *,
    settings: Settings | None = None,
    runs_root: Path | None = None,
    use_agents: bool = False,
    on_event=None,
) -> RunState:
    """Clone, inspect, plan, run in Docker, repair, verdict, reports."""
    cfg = settings or load_settings()
    run_dir = create_run(url, runs_root=runs_root)
    state = RunState(url=url, run_directory=str(run_dir.path))
    container_id: str | None = None

    def emit(kind: str, message: str) -> None:
        event = make_event(run_dir.path.name, kind, message)
        publish(run_dir, event)
        if on_event is not None:
            on_event(event)

    try:
        emit("phase", "clone")
        GitCloneTool().run(CloneRequest(url=url, run_dir=run_dir, settings=cfg))

        emit("phase", "inspect")
        facts = _inspect(run_dir, cfg, use_agents=use_agents, emit=emit)
        state.facts = facts

        if "secret" in facts.blockers or "gpu" in facts.blockers:
            state.verdict = decide_verdict(facts, None, [], 0)
            emit("verdict", state.verdict.label)
            _write_reports(run_dir, state)
            return state

        emit("phase", "plan")
        try:
            plan = _plan(facts, cfg, use_agents=use_agents, emit=emit)
        except InsufficientReadmeError:
            state.verdict = decide_verdict(facts, None, [], 0)
            emit("verdict", state.verdict.label)
            _write_reports(run_dir, state)
            return state
        state.plan = plan

        emit("phase", "sandbox")
        container_id = start(run_dir, plan, cfg)

        def run_commands(current: RunPlan) -> list[AttemptLog]:
            attempts: list[AttemptLog] = []
            for command in current.setup_commands + current.run_commands:
                emit("command", command.script)

                def on_line(kind: str, line: str, _cmd=command.script) -> None:
                    emit("log", f"{kind}: {line}")

                try:
                    attempt = docker_exec(
                        container_id,
                        command.script,
                        timeout_s=command.timeout_s,
                        phase=command.phase,
                        on_line=on_line,
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
                    break
            return attempts

        # Prefer Driver agent when enabled; otherwise deterministic run + repair.
        if use_agents:
            from readme2run.agents.crew import run_driver_crew

            attempts = run_driver_crew(
                plan=plan,
                container_id=container_id,
                run_dir=run_dir,
                settings=cfg,
                emit=emit,
            )
            state.attempts.extend(attempts)
            # Count pip install repairs roughly from setup growth.
            state.repair_count = max(0, len(plan.setup_commands))
        else:
            state.attempts.extend(run_commands(plan))
            plan, container_id = repair_loop(
                state=state,
                plan=plan,
                run_dir=run_dir,
                settings=cfg,
                container_id=container_id,
                run_commands=run_commands,
                ask_driver=default_driver,
            )
            state.plan = plan
            if not container_id:
                container_id = start(run_dir, plan, cfg)
                state.attempts.extend(run_commands(plan))

        state.verdict = decide_verdict(facts, plan, state.attempts, state.repair_count)
        if use_agents:
            from readme2run.agents.crew import write_evidence

            try:
                state.verdict.evidence = write_evidence(state)
            except Exception:
                pass
        emit("verdict", state.verdict.label)
        _write_reports(run_dir, state)
        return state
    finally:
        if container_id:
            stop(container_id)


def _inspect(run_dir: RunDir, cfg: Settings, *, use_agents: bool, emit) -> object:
    if use_agents:
        try:
            from readme2run.agents.crew import run_inspector

            facts = run_inspector(run_dir.repo, cfg)
            if facts.tree or facts.readme.commands:
                return facts
        except Exception as exc:  # noqa: BLE001
            emit("phase", f"inspector fallback: {exc}")
    return inspect_repo(run_dir.repo, cfg)


def _plan(facts, cfg: Settings, *, use_agents: bool, emit):
    fallback = select_plan(facts, cfg)
    if use_agents:
        try:
            from readme2run.agents.crew import run_architect

            plan = run_architect(facts, cfg)
            if plan is not None and plan.run_commands:
                return plan
            emit("phase", "architect fallback: empty plan")
        except Exception as exc:  # noqa: BLE001
            emit("phase", f"architect fallback: {exc}")
    return fallback


def _write_reports(run_dir: RunDir, state: RunState) -> None:
    write_json_report(run_dir.path, state)
    write_markdown_report(run_dir.path, state)
