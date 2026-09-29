from readme2run.guardrails.prompt_data import UNTRUSTED_END, UNTRUSTED_START, wrap_untrusted


def test_wrapped_readme_contains_the_data_markers() -> None:
    """Repo text is wrapped so a prompt can treat it as data."""
    wrapped = wrap_untrusted("# Hello\npython main.py")

    assert UNTRUSTED_START in wrapped
    assert UNTRUSTED_END in wrapped
    assert "# Hello\npython main.py" in wrapped
