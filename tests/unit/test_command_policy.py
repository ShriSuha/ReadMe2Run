from readme2run.guardrails.command_policy import command_policy


def test_pip_install_is_allowed() -> None:
    """An ordinary install command may run in the container."""
    decision = command_policy("python -m pip install rich")

    assert decision.allowed
    assert decision.reason == ""


def test_sudo_is_rejected() -> None:
    """sudo is rejected before Docker sees the command."""
    decision = command_policy("sudo apt-get install git")

    assert not decision.allowed
    assert decision.reason


def test_docker_socket_mount_is_rejected() -> None:
    """Mounting the Docker socket would give the container control of the host."""
    decision = command_policy(
        "docker run -v /var/run/docker.sock:/var/run/docker.sock alpine"
    )

    assert not decision.allowed
    assert "socket" in decision.reason


def test_privileged_and_root_mount_and_outside_redirect_are_rejected() -> None:
    """The other blocked shapes are privileged mode, host root, and a write outside /work."""
    assert not command_policy("docker run --privileged alpine").allowed
    assert not command_policy("docker run -v /:/host alpine").allowed
    assert not command_policy("echo hi > /tmp/out.txt").allowed

    inside = command_policy("echo hi > /work/out.txt")
    assert inside.allowed
