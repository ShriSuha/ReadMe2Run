import re

from pydantic import BaseModel

from readme2run.configurations.loader import Settings
from readme2run.guardrails.command_policy import command_policy
from readme2run.schemas.repair import RepairAction

# Shell words that end the install command and start something else.
_SHELL_BREAKS = {"&&", "||", ";", "|"}


class RepairDecision(BaseModel):
    """The result of checking one RepairAction.

    allowed is true when the repair may be applied. reason explains a
    rejection and is empty when the repair is allowed. This object does
    not run the repair.
    """

    allowed: bool
    reason: str = ""


def repair_policy(action: RepairAction, settings: Settings) -> RepairDecision:
    """Allow or reject one proposed repair.

    stop is always allowed. set_env is allowed when it carries variables.
    insert_setup_command is allowed only when the command passes
    command_policy, does not edit project source, and, if it is
    apt-get install, every package is on the allowlist. The model does
    not get a free shell through this door.
    """
    if action.kind == "stop":
        return RepairDecision(allowed=True)
    if action.kind == "set_env":
        return _check_env(action)
    if action.command is None:
        return _reject("insert_setup_command needs a command")
    script = action.command.script
    command_decision = command_policy(script)
    if not command_decision.allowed:
        return _reject(command_decision.reason)
    if _edits_source(script):
        return _reject("repairs may not edit project source")
    packages = _apt_packages(script)
    if packages is None:
        return RepairDecision(allowed=True)
    if not packages:
        return _reject("apt-get install listed no packages")
    blocked = [name for name in packages if name not in settings.policies.apt_allowlist]
    if blocked:
        names = ", ".join(blocked)
        return _reject(f"apt package is not on the allowlist: {names}")
    return RepairDecision(allowed=True)


def _check_env(action: RepairAction) -> RepairDecision:
    """Allow set_env only when it actually sets at least one variable."""
    if not action.env:
        return _reject("set_env needs environment variables")
    return RepairDecision(allowed=True)


def _reject(reason: str) -> RepairDecision:
    """Build a rejection. Callers read allowed and reason."""
    return RepairDecision(allowed=False, reason=reason)


def _edits_source(script: str) -> bool:
    """True when the command rewrites a project file or applies a patch.

    sed -i edits a file in place. git apply and patch change tracked
    source. Writing a .patch file is the same kind of change.
    """
    if re.search(r"\bsed\b", script) and re.search(r"(?:^|\s)(?:-i\b|--in-place\b)", script):
        return True
    if re.search(r"\bgit\s+apply\b", script) or re.search(r"(?:^|[;&|]\s*)patch\b", script):
        return True
    return re.search(r">\s*\S+\.patch\b", script) is not None


def _apt_packages(script: str) -> list[str] | None:
    """Return package names when the command is apt-get install.

    None means this is not an apt-get install command, so the allowlist
    does not apply. Flags such as -y are skipped. Shell operators end the
    package list.
    """
    match = re.search(r"\bapt-get\s+install\b(.*)", script)
    if match is None:
        return None
    packages: list[str] = []
    for token in match.group(1).split():
        if token in _SHELL_BREAKS:
            break
        if token.startswith("-"):
            continue
        packages.append(token.strip("'\""))
    return packages
