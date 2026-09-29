"""Step 28 stand-in: four fixture runs covering python, repair, discovery stacks.

Public GitHub URLs can be tried with:
  uv run readme2run run https://github.com/org/repo
"""

from pathlib import Path

from readme2run.configurations.loader import load_settings
from readme2run.orchestration.flow import run_flow
from readme2run.schemas.state import RunState
from readme2run.schemas.verdict import Verdict


LABELS = {
    "ran_as_documented",
    "ran_after_repair",
    "blocked_missing_secret",
    "blocked_needs_gpu_or_data",
    "readme_insufficient",
    "failed",
}


def test_four_fixture_reports(tmp_path: Path) -> None:
    settings = load_settings().model_copy(update={"allow_file_urls": True})
    fixtures = [
        Path("tests/fixtures/hello").resolve(),
        Path("tests/fixtures/missing_dep").resolve(),
        Path("tests/fixtures/full_stack").resolve(),
        Path("tests/fixtures/ci_only").resolve(),
    ]
    # full_stack and ci_only are not git repos for clone — init them quickly if needed
    import subprocess

    for fixture in fixtures:
        if not (fixture / ".git").exists():
            subprocess.run(["git", "init"], cwd=fixture, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=fixture, check=True, capture_output=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.email=t@e.com",
                    "-c",
                    "user.name=t",
                    "commit",
                    "-m",
                    "init",
                ],
                cwd=fixture,
                check=True,
                capture_output=True,
            )

    for fixture in fixtures:
        # full_stack has secret blocker → blocked_missing_secret before run
        state = run_flow(
            fixture.as_uri(),
            settings=settings,
            runs_root=tmp_path / fixture.name,
            use_agents=False,
        )
        assert state.verdict is not None
        assert state.verdict.label in LABELS
        report_md = Path(state.run_directory) / "report.md"
        report_json = Path(state.run_directory) / "report.json"
        assert report_md.is_file()
        assert report_json.is_file()
        loaded = RunState.model_validate_json(report_json.read_text())
        assert loaded.verdict is not None
        assert isinstance(loaded.verdict, Verdict)
