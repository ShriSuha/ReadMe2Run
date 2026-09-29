from pydantic import BaseModel

from readme2run.configurations.loader import Settings

# policies.yaml says megabytes. Count them as 1024 x 1024 bytes.
_BYTES_PER_MB = 1024 * 1024


class ResourceDecision(BaseModel):
    """The result of checking one size or timeout against Settings.

    allowed is true when the value is within the cap. reason explains a
    rejection and is empty when the value is allowed.
    """

    allowed: bool
    reason: str = ""


def check_repo_size(size_bytes: int, settings: Settings) -> ResourceDecision:
    """Reject a checkout larger than the repo size cap."""
    cap_bytes = settings.policies.repo_size_cap_mb * _BYTES_PER_MB
    if size_bytes > cap_bytes:
        return _reject(
            f"repo size {size_bytes} bytes is above the cap of {settings.policies.repo_size_cap_mb} MB"
        )
    return ResourceDecision(allowed=True)


def check_tree_length(path_count: int, settings: Settings) -> ResourceDecision:
    """Reject a file listing longer than the tree cap."""
    cap = settings.policies.tree_cap_paths
    if path_count > cap:
        return _reject(f"tree length {path_count} is above the cap of {cap} paths")
    return ResourceDecision(allowed=True)


def check_readme_length(character_count: int, settings: Settings) -> ResourceDecision:
    """Reject README text longer than the character cap."""
    cap = settings.policies.readme_cap_characters
    if character_count > cap:
        return _reject(f"README length {character_count} is above the cap of {cap} characters")
    return ResourceDecision(allowed=True)


def check_timeout(timeout_s: int, settings: Settings, *, phase: str) -> ResourceDecision:
    """Reject a timeout above the ceiling for that phase.

    A setup command uses the build/install ceiling. Any other phase uses
    the normal command ceiling. Both numbers come from sandbox settings.
    """
    if phase == "setup":
        ceiling = settings.sandbox.build_install_timeout
    else:
        ceiling = settings.sandbox.command_timeout
    if timeout_s > ceiling:
        return _reject(f"timeout {timeout_s}s is above the {phase} ceiling of {ceiling}s")
    return ResourceDecision(allowed=True)


def _reject(reason: str) -> ResourceDecision:
    """Build a rejection. Callers read allowed and reason."""
    return ResourceDecision(allowed=False, reason=reason)
