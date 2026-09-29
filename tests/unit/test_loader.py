from readme2run.configurations.loader import load_settings


def test_load_settings_reads_model_timeout_and_repairs() -> None:
    """The real yaml files produce the model, timeout, and repair cap."""
    settings = load_settings()

    assert settings.model.model == "qwen2.5:14b"
    assert settings.sandbox.command_timeout == 300
    assert settings.policies.max_repairs == 5
