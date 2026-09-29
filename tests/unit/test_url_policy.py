from readme2run.configurations.loader import load_settings
from readme2run.guardrails.url_policy import url_policy


def test_https_url_is_allowed() -> None:
    """A normal GitHub https URL may be cloned."""
    settings = load_settings()

    decision = url_policy("https://github.com/org/repo", settings)

    assert decision.allowed
    assert decision.reason == ""


def test_ssh_url_is_rejected() -> None:
    """An ssh URL is rejected before anything tries to clone it."""
    settings = load_settings()

    decision = url_policy("ssh://git@github.com/org/repo.git", settings)

    assert not decision.allowed
    assert decision.reason


def test_file_url_requires_the_test_flag() -> None:
    """file:// is rejected until the test flag on Settings is turned on."""
    settings = load_settings()

    blocked = url_policy("file:///tmp/hello", settings)
    assert not blocked.allowed

    allowed = url_policy(
        "file:///tmp/hello",
        settings.model_copy(update={"allow_file_urls": True}),
    )
    assert allowed.allowed
