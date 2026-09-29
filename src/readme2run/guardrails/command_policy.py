import re

from pydantic import BaseModel

# A redirect operator, then the path it writes to.
_REDIRECT = re.compile(r"(?:&>>|&>|>>|>\|?)\s*([^\s;|&]+)")
# Docker -v /: or --volume /: mounts the host root.
_ROOT_VOLUME = re.compile(r"(?:-v|--volume)(?:=|\s+)/:")
# --mount source=/ mounts the host root. source=/work does not match.
_ROOT_SOURCE = re.compile(r"source=/(?:,|\s|$)")


class CommandDecision(BaseModel):
    """The result of checking one shell command.

    allowed is true when the command may run in the container. reason explains
    a rejection and is empty when the command is allowed. This object does not
    run the command.
    """

    allowed: bool
    reason: str = ""


def command_policy(command: str) -> CommandDecision:
    """Allow or reject a shell command before it enters the container.

    The model and the README both produce command strings. This function is
    the gate in front of Docker. It rejects the Docker socket, sudo,
    privileged mode, a mount of the host root /, and a redirect that writes
    outside /work. It does not run the command or call a model.
    """
    if re.search(r"\bsudo\b", command):
        return _reject("sudo is not allowed")
    if "docker.sock" in command:
        return _reject("mounting the Docker socket is not allowed")
    if "--privileged" in command:
        return _reject("privileged mode is not allowed")
    if _mounts_host_root(command):
        return _reject("mounting the host root / is not allowed")
    outside = _redirect_outside_work(command)
    if outside is not None:
        return _reject(f"redirect writes outside /work: {outside}")
    return CommandDecision(allowed=True)


def _reject(reason: str) -> CommandDecision:
    """Build a rejection. Callers read allowed and reason."""
    return CommandDecision(allowed=False, reason=reason)


def _mounts_host_root(command: str) -> bool:
    """True when the command bind-mounts the host directory /."""
    return _ROOT_VOLUME.search(command) is not None or _ROOT_SOURCE.search(command) is not None


def _redirect_outside_work(command: str) -> str | None:
    """Return the first redirect target that is not inside /work."""
    for target in _REDIRECT.findall(command):
        path = target.strip("'\"")
        if path.startswith("&"):
            continue
        if not _inside_work(path):
            return path
    return None


def _inside_work(path: str) -> bool:
    """True when a redirect stays in the container work directory.

    A relative path such as out.txt is inside /work, because the command
    runs there. An absolute path must be /work or a file under it.
    A path with .. can climb out, so it is rejected.
    """
    if ".." in path.split("/"):
        return False
    if path.startswith("/"):
        return path == "/work" or path.startswith("/work/")
    return True
