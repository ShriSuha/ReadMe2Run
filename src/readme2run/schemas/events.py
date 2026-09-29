from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class RunEvent(BaseModel):
    """One message published while a run is in progress.

    The flow publishes these. The terminal prints them. RunState keeps
    the lasting result; events are the live story of how it got there.
    """

    run_id: str
    timestamp: datetime
    kind: Literal[
        # A boundary, such as clone, inspect, plan, or run.
        "phase",
        # One line of command output.
        "log",
        # A command that is about to run or has finished.
        "command",
        # A repair that was applied after a failure.
        "repair",
        # The final label for the run.
        "verdict",
    ]
    message: str
