"""Stream command output from a running container."""

from __future__ import annotations

import concurrent.futures
from collections.abc import Iterator
from typing import Any

import docker


def exec_stream(container_id: str, script: str, timeout_s: int) -> Iterator[tuple[str, Any]]:
    """Yield (\"stdout\"|\"stderr\", line) then (\"exit\", code).

    On timeout, kill processes in the container and yield exit code 124.
    """
    client = docker.from_env()
    container = client.containers.get(container_id)

    def run() -> tuple[int, bytes, bytes]:
        exit_code, output = container.exec_run(
            ["/bin/sh", "-lc", script],
            demux=True,
        )
        out, err = output if isinstance(output, tuple) else (output, b"")
        return int(exit_code), out or b"", err or b""

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run)
        try:
            code, out, err = future.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError:
            try:
                container.exec_run(["/bin/sh", "-lc", "kill -9 -1"])
            except Exception:
                pass
            yield ("exit", 124)
            return

    for line in out.decode("utf-8", errors="replace").splitlines():
        yield ("stdout", line)
    for line in err.decode("utf-8", errors="replace").splitlines():
        yield ("stderr", line)
    yield ("exit", code)
