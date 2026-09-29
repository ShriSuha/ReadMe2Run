"""Repair loop: rerun with Driver-proposed fixes until success or budget."""

from __future__ import annotations

from collections.abc import Callable

from readme2run.configurations.loader import Settings
from readme2run.guardrails.repair_policy import repair_policy
from readme2run.orchestration.events import make_event, publish
from readme2run.schemas.attempt import AttemptLog
from readme2run.schemas.plan import Command, RunPlan
from readme2run.schemas.repair import RepairAction
from readme2run.schemas.state import RunState
from readme2run.tools.docker_exec import docker_exec
from readme2run.tools.git_clone import ToolRejected
from readme2run.workspace.run_dir import RunDir


DriverFn = Callable[[AttemptLog, RunPlan], RepairAction]
RunCommandsFn = Callable[[RunPlan], list[AttemptLog]]


def default_driver(attempt: AttemptLog, plan: RunPlan) -> RepairAction:
    """Heuristic repair when no CrewAI Driver is wired yet."""
    import re

    err = attempt.stderr + "\n" + attempt.stdout
    match = re.search(r"ModuleNotFoundError:\s*No module named ['\"]([^'\"]+)['\"]", err)
    if match:
        module = match.group(1).split(".")[0]
        return RepairAction(
            kind="insert_setup_command",
            command=Command(
                script=f"python -m pip install --no-cache-dir {module}",
                timeout_s=300,
                purpose=f"install missing module {module}",
                phase="setup",
            ),
            reason=f"missing module {module}",
        )
    return RepairAction(kind="stop", reason="no automatic repair available")



def repair_loop(
    *,
    state: RunState,
    plan: RunPlan,
    run_dir: RunDir,
    settings: Settings,
    container_id: str,
    run_commands: RunCommandsFn,
    ask_driver: DriverFn = default_driver,
) -> tuple[RunPlan, str]:
    """Apply repairs until success, stop, or max_repairs.

    Returns the (possibly updated) plan and the latest container id
    (may change when env requires a recreate — caller handles recreate).
    """
    while True:
        if not state.attempts:
            break
        last = state.attempts[-1]
        if last.exit_code == 0:
            break
        if state.repair_count >= settings.policies.max_repairs:
            break
        action = ask_driver(last, plan)
        decision = repair_policy(action, settings)
        if not decision.allowed or action.kind == "stop":
            if not decision.allowed:
                action = RepairAction(kind="stop", reason=decision.reason)
            publish(
                run_dir,
                make_event(run_dir.path.name, "repair", f"stop: {action.reason}"),
            )
            break
        state.repair_count += 1
        publish(
            run_dir,
            make_event(
                run_dir.path.name,
                "repair",
                f"attempt {state.repair_count}: {action.kind} {action.reason}",
            ),
        )
        if action.kind == "insert_setup_command" and action.command is not None:
            plan = plan.model_copy(
                update={"setup_commands": [*plan.setup_commands, action.command]}
            )
            try:
                attempt = docker_exec(
                    container_id,
                    action.command.script,
                    timeout_s=action.command.timeout_s,
                    phase="setup",
                )
            except ToolRejected as exc:
                state.attempts.append(
                    AttemptLog(
                        command=action.command.script,
                        exit_code=1,
                        stdout="",
                        stderr=exc.reason,
                        duration=0.0,
                        phase="setup",
                    )
                )
                break
            state.attempts.append(attempt)
            if attempt.exit_code != 0:
                continue
            # Rerun from the failed phase: re-run run commands.
            state.attempts.extend(run_commands(plan))
            continue
        if action.kind == "set_env" and action.env:
            plan = plan.model_copy(update={"env": {**plan.env, **action.env}})
            # Caller recreates container when env changes; signal via empty id.
            return plan, ""
    return plan, container_id
