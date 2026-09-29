from typing import Literal

from pydantic import BaseModel

from readme2run.schemas.plan import Command


class RepairAction(BaseModel):
    """One small change the driver may make after a failed AttemptLog.

    insert_setup_command uses command. set_env uses env.
    stop means give up. reason says why this action was chosen.
    Applying one of these increases RunState.repair_count.
    """

    kind: Literal["insert_setup_command", "set_env", "stop"]
    command: Command | None = None
    env: dict[str, str] | None = None
    reason: str
