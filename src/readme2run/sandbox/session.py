"""Start and stop a Docker container for one run.

Only this package talks to the Docker SDK. Agents never import it.
"""

from __future__ import annotations

import docker
from docker.errors import NotFound

from readme2run.configurations.loader import Settings, load_settings
from readme2run.guardrails.secrets import host_env_for_container
from readme2run.schemas.plan import RunPlan
from readme2run.workspace.run_dir import RunDir


def start(workspace: RunDir, plan: RunPlan, settings: Settings | None = None) -> str:
    """Start a long-lived container with the repo mounted at /work.

    Returns the container id. The process inside is sleep infinity so
    later exec calls can run commands.
    """
    cfg = settings or load_settings()
    client = docker.from_env()
    image = plan.base_image or cfg.sandbox.images["python"]
    if plan.dockerfile_path:
        # Build from the repo Dockerfile when the plan asks for it.
        built, _ = client.images.build(
            path=str(workspace.repo),
            dockerfile=plan.dockerfile_path,
            rm=True,
            tag=f"readme2run-{workspace.path.name}".lower()[:64],
        )
        image = built.id
    env = {**(plan.env or {}), **host_env_for_container()}
    container = client.containers.run(
        image=image,
        command=["sleep", "infinity"],
        detach=True,
        working_dir=plan.workdir or "/work",
        volumes={str(workspace.repo.resolve()): {"bind": "/work", "mode": "rw"}},
        environment=env,
        mem_limit=cfg.sandbox.memory,
        nano_cpus=cfg.sandbox.nano_cpus,
        network_disabled=False,
        cap_drop=["ALL"],
        security_opt=["no-new-privileges"],
        user=_default_user(image, client),
    )
    return container.id


def stop(container_id: str) -> None:
    """Remove the container. Safe to call after failures."""
    client = docker.from_env()
    try:
        container = client.containers.get(container_id)
    except NotFound:
        return
    try:
        container.remove(force=True)
    except Exception:
        pass


def _default_user(image: str, client: docker.DockerClient) -> str | None:
    """Use a non-root user when the image defines one."""
    try:
        meta = client.images.get(image)
    except Exception:
        return None
    user = (meta.attrs.get("Config") or {}).get("User") or ""
    return user or None
