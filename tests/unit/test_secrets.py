from readme2run.guardrails.secrets import host_env_for_container, redact_secrets


def test_github_token_in_a_log_line_is_redacted() -> None:
    """The token value is hidden. The variable name can stay."""
    line = "clone failed: GITHUB_TOKEN=ghp_example"

    redacted = redact_secrets(line)

    assert "ghp_example" not in redacted
    assert "GITHUB_TOKEN=***" in redacted


def test_host_environment_is_not_copied_into_the_container() -> None:
    """The container receives no variables from this machine."""
    assert host_env_for_container() == {}
