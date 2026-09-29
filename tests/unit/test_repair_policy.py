from readme2run.configurations.loader import load_settings
from readme2run.guardrails.repair_policy import repair_policy
from readme2run.schemas.plan import Command
from readme2run.schemas.repair import RepairAction


def _install(script: str) -> RepairAction:
    return RepairAction(
        kind="insert_setup_command",
        command=Command(
            script=script,
            timeout_s=300,
            purpose="install a package",
            phase="setup",
        ),
        reason="a dependency is missing",
    )


def test_allowlisted_apt_package_is_accepted() -> None:
    """git is on the apt allowlist, so the install may be added."""
    decision = repair_policy(_install("apt-get install -y git"), load_settings())

    assert decision.allowed
    assert decision.reason == ""


def test_apt_package_off_the_allowlist_is_rejected() -> None:
    """nmap is not on the allowlist, so the install is rejected."""
    decision = repair_policy(_install("apt-get install -y nmap"), load_settings())

    assert not decision.allowed
    assert "nmap" in decision.reason


def test_stop_is_accepted_and_source_edits_are_rejected() -> None:
    """stop always passes. A command that edits a project file does not."""
    settings = load_settings()
    stop = RepairAction(kind="stop", reason="the traceback is a project bug")
    assert repair_policy(stop, settings).allowed

    sed = repair_policy(_install("sed -i 's/a/b/' main.py"), settings)
    assert not sed.allowed

    sudo = repair_policy(_install("sudo apt-get install git"), settings)
    assert not sudo.allowed
