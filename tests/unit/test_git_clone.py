import subprocess
from pathlib import Path

import pytest

from readme2run.configurations.loader import load_settings
from readme2run.tools.git_clone import CloneRequest, GitCloneTool, ToolRejected
from readme2run.workspace.run_dir import create_run


def _fixture_repo(path: Path) -> None:
    """Make a one-commit git repo so a file:// clone has something to copy."""
    path.mkdir()
    (path / "hello.txt").write_text("hello-readme2run\n")
    commands = [
        ["git", "init"],
        ["git", "add", "hello.txt"],
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test",
            "commit",
            "-m",
            "init",
        ],
    ]
    for command in commands:
        subprocess.run(command, cwd=path, check=True, capture_output=True, text=True)


def test_file_url_clone_copies_the_fixture_files(tmp_path: Path) -> None:
    """With the test flag on, a local file:// repo is cloned into RunDir.repo."""
    fixture = tmp_path / "fixture"
    _fixture_repo(fixture)
    settings = load_settings().model_copy(update={"allow_file_urls": True})
    run = create_run(fixture.as_uri(), runs_root=tmp_path / "runs")

    result = GitCloneTool().run(
        CloneRequest(url=fixture.as_uri(), run_dir=run, settings=settings)
    )

    assert result.path == run.repo
    assert (result.path / "hello.txt").read_text() == "hello-readme2run\n"


def test_ssh_url_is_rejected_without_calling_git(tmp_path: Path) -> None:
    """An ssh URL fails in url_policy. git is not started."""
    calls: list[list[str]] = []

    def run_git(args: list[str]) -> None:
        calls.append(args)

    url = "ssh://git@github.com/org/repo.git"
    run = create_run(url, runs_root=tmp_path)
    request = CloneRequest(url=url, run_dir=run, settings=load_settings())

    with pytest.raises(ToolRejected) as rejected:
        GitCloneTool(run_git=run_git).run(request)

    assert "ssh" in rejected.value.reason
    assert calls == []
