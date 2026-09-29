"""Command-line entry: run, runs, show."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from readme2run.cli.live_view import LiveView
from readme2run.configurations.loader import load_settings
from readme2run.orchestration.events import iter_events
from readme2run.orchestration.flow import run_flow
from readme2run.workspace.run_dir import RunDir


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="readme2run",
        description="Read a repository README and run it.",
    )
    commands = parser.add_subparsers(dest="command")

    run_parser = commands.add_parser("run", help="Run a repository from its URL")
    run_parser.add_argument("url", help="https:// or file:// repository URL")
    run_parser.add_argument(
        "--allow-file-urls",
        action="store_true",
        help="Allow file:// URLs (tests and local fixtures)",
    )
    run_parser.add_argument(
        "--agents",
        action="store_true",
        help="Use CrewAI agents (Inspector, Architect, Driver, Analyst)",
    )

    commands.add_parser("runs", help="List past runs")
    show_parser = commands.add_parser("show", help="Show one run")
    show_parser.add_argument("run_id", help="Run folder name")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return
    if args.command == "run":
        _cmd_run(args)
    elif args.command == "runs":
        _cmd_runs()
    elif args.command == "show":
        _cmd_show(args.run_id)


def _cmd_run(args: argparse.Namespace) -> None:
    settings = load_settings().model_copy(update={"allow_file_urls": args.allow_file_urls})
    view = LiveView()
    state = run_flow(
        args.url,
        settings=settings,
        use_agents=args.agents,
        on_event=view.handle,
    )
    label = state.verdict.label if state.verdict else "unknown"
    Console().print(f"[bold]done[/] {label}  ({state.run_directory})")
    if state.verdict and state.verdict.label in {"failed", "readme_insufficient"}:
        sys.exit(1)


def _runs_root() -> Path:
    return Path(load_settings().app.runs_dir).expanduser()


def _cmd_runs() -> None:
    root = _runs_root()
    console = Console()
    table = Table("run id", "url", "verdict", "path")
    if not root.is_dir():
        console.print("No runs yet.")
        return
    for path in sorted(root.iterdir(), reverse=True):
        if not path.is_dir():
            continue
        report = path / "report.json"
        url = ""
        label = ""
        if report.is_file():
            data = json.loads(report.read_text(encoding="utf-8"))
            url = data.get("url", "")
            verdict = data.get("verdict") or {}
            label = verdict.get("label", "")
        table.add_row(path.name, url, label, str(path))
    console.print(table)


def _cmd_show(run_id: str) -> None:
    path = _runs_root() / run_id
    console = Console()
    if not path.is_dir():
        console.print(f"Run not found: {run_id}")
        sys.exit(1)
    report = path / "report.json"
    if report.is_file():
        data = json.loads(report.read_text(encoding="utf-8"))
        verdict = data.get("verdict") or {}
        console.print(f"[bold]verdict[/] {verdict.get('label')}")
        console.print(verdict.get("evidence", ""))
    run_dir = RunDir(
        path=path,
        repo=path / "repo",
        logs=path / "logs",
        events_path=path / "events.jsonl",
    )
    console.print("[bold]events[/]")
    for event in iter_events(run_dir):
        console.print(f"{event.timestamp.isoformat()} {event.kind}: {event.message}")


if __name__ == "__main__":
    main()
