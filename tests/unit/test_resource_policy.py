from readme2run.configurations.loader import load_settings
from readme2run.guardrails.resource_policy import (
    check_readme_length,
    check_repo_size,
    check_timeout,
    check_tree_length,
)


def test_sizes_and_timeouts_use_the_settings_caps() -> None:
    """Values at the cap are allowed. One past the cap is rejected."""
    settings = load_settings()
    one_mb = 1024 * 1024

    assert check_repo_size(200 * one_mb, settings).allowed
    assert not check_repo_size(201 * one_mb, settings).allowed
    assert check_tree_length(200, settings).allowed
    assert not check_tree_length(201, settings).allowed
    assert check_readme_length(40000, settings).allowed
    assert not check_readme_length(40001, settings).allowed
    assert check_timeout(300, settings, phase="run").allowed
    assert not check_timeout(301, settings, phase="run").allowed
    assert check_timeout(900, settings, phase="setup").allowed
    assert not check_timeout(901, settings, phase="setup").allowed
