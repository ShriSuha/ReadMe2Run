from pathlib import Path

from readme2run.discovery import inspect_repo


def test_hello_fixture_readme_and_tree() -> None:
    facts = inspect_repo(Path("tests/fixtures/hello"))
    assert "python main.py" in facts.readme.commands
    assert "main.py" in facts.tree


def test_full_stack_manifest_dockerfile_ci_and_secret() -> None:
    facts = inspect_repo(Path("tests/fixtures/full_stack"))
    assert "requirements.txt" in facts.manifests
    assert facts.dockerfile_path == "Dockerfile"
    assert "pytest" in facts.ci_commands
    assert "secret" in facts.blockers
