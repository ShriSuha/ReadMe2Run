from pydantic import BaseModel, Field

from readme2run.schemas.attempt import AttemptLog
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import RunPlan
from readme2run.schemas.verdict import Verdict


class RunState(BaseModel):
    """Everything known about one run, gathered in a single object.

    The pieces connect like this: discovery fills facts, planning builds
    plan, each command appends an attempt, a repair raises repair_count,
    and the finished run gets a verdict.
    """

    # The address the user asked to run, such as a GitHub URL.
    url: str
    # Folder on this machine where this run's repo, logs, and report are saved.
    run_directory: str
    facts: RepoFacts = Field(default_factory=RepoFacts)
    plan: RunPlan | None = None
    attempts: list[AttemptLog] = Field(default_factory=list)
    # How many repairs have been applied. Stops at the cap in policies.yaml.
    repair_count: int = 0
    verdict: Verdict | None = None
