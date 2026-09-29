"""Terminal view that subscribes to RunEvent lines."""

from __future__ import annotations

from rich.console import Console

from readme2run.schemas.events import RunEvent


class LiveView:
    """Print phase, command, and log tails as events arrive."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.phase = ""
        self.command = ""

    def handle(self, event: RunEvent) -> None:
        if event.kind == "phase":
            self.phase = event.message
            self.console.print(f"[bold cyan]phase[/] {event.message}")
        elif event.kind == "command":
            self.command = event.message
            self.console.print(f"[bold yellow]command[/] {event.message}")
        elif event.kind == "log":
            self.console.print(event.message)
        elif event.kind == "repair":
            self.console.print(f"[bold magenta]repair[/] {event.message}")
        elif event.kind == "verdict":
            self.console.print(f"[bold green]verdict[/] {event.message}")
        else:
            self.console.print(event.message)
