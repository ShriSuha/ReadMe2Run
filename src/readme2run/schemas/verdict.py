from typing import Literal

from pydantic import BaseModel, Field

from readme2run.schemas.attempt import AttemptLog


class Verdict(BaseModel):
    """The final label for a run, the evidence behind it, and the attempts.

    Python chooses the label from the facts and the logs. The model does not.
    """

    label: Literal[
        # The documented commands exited 0 and no repair was needed.
        "ran_as_documented",
        # The commands exited 0 only after at least one repair.
        "ran_after_repair",
        # The repo needs a secret, such as an API key, that this tool does not have.
        "blocked_missing_secret",
        # The repo needs a GPU or data this sandbox cannot provide.
        "blocked_needs_gpu_or_data",
        # The README and CI did not contain a command to run.
        "readme_insufficient",
        # A command still failed after the repairs that were allowed.
        "failed",
    ]
    # The paragraph a person reads, explaining why this label was chosen.
    evidence: str
    attempts: list[AttemptLog] = Field(default_factory=list)
