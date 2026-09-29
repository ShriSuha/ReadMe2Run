from pydantic import BaseModel


class AttemptLog(BaseModel):
    """What one command printed and whether it succeeded.

    A failed attempt is what a RepairAction tries to fix. These logs are
    stored on RunState and copied onto the Verdict.
    """

    command: str
    exit_code: int
    stdout: str
    stderr: str
    # How long the command ran, in seconds.
    duration: float
    phase: str
