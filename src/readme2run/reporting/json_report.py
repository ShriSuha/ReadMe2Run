"""JSON report writer."""

from pathlib import Path

from readme2run.reporting.markdown_report import write_json_report
from readme2run.schemas.state import RunState

__all__ = ["write_json_report"]


def write_report_json(run_directory: Path | str, state: RunState) -> Path:
    return write_json_report(run_directory, state)
