"""Run one shell command in the sandbox after the command guardrail."""

from __future__ import annotations

import time

from readme2run.guardrails.command_policy import command_policy
from readme2run.guardrails.secrets import redact_secrets
from readme2run.sandbox.stream import exec_stream
from readme2run.schemas.attempt import AttemptLog
from readme2run.tools.git_clone import ToolRejected


def docker_exec(
    container_id: str,
    script: str,
    *,
    timeout_s: int,
    phase: str = "run",
    on_line=None,
) -> AttemptLog:
    """Guardrail → stream → redact → AttemptLog.

    Raises ToolRejected when the command policy refuses the script.
    """
    decision = command_policy(script)
    if not decision.allowed:
        raise ToolRejected(decision.reason)

    started = time.monotonic()
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    exit_code = 1
    for kind, value in exec_stream(container_id, script, timeout_s):
        if kind == "exit":
            exit_code = int(value)
            break
        line = str(value)
        if on_line is not None:
            on_line(kind, line)
        if kind == "stdout":
            stdout_parts.append(line)
        else:
            stderr_parts.append(line)
    duration = time.monotonic() - started
    return AttemptLog(
        command=script,
        exit_code=exit_code,
        stdout=redact_secrets("\n".join(stdout_parts)),
        stderr=redact_secrets("\n".join(stderr_parts)),
        duration=duration,
        phase=phase,
    )
