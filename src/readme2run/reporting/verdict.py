"""Compute the final verdict label from facts and attempts."""

from readme2run.schemas.attempt import AttemptLog
from readme2run.schemas.facts import RepoFacts
from readme2run.schemas.plan import RunPlan
from readme2run.schemas.verdict import Verdict


def decide_verdict(
    facts: RepoFacts,
    plan: RunPlan | None,
    attempts: list[AttemptLog],
    repair_count: int,
) -> Verdict:
    """Pick the first matching label. The model does not choose this."""
    if "secret" in facts.blockers:
        return Verdict(
            label="blocked_missing_secret",
            evidence="The repository requires a secret this tool does not provide.",
            attempts=attempts,
        )
    if "gpu" in facts.blockers:
        return Verdict(
            label="blocked_needs_gpu_or_data",
            evidence="The repository appears to need a GPU or data this sandbox cannot provide.",
            attempts=attempts,
        )
    if plan is None or not plan.run_commands:
        return Verdict(
            label="readme_insufficient",
            evidence="No run command was found in the README or CI.",
            attempts=attempts,
        )
    if not attempts or attempts[-1].exit_code != 0:
        return Verdict(
            label="failed",
            evidence="The last command exited non-zero after the allowed repairs.",
            attempts=attempts,
        )
    if repair_count == 0:
        return Verdict(
            label="ran_as_documented",
            evidence="The documented commands exited 0 without repairs.",
            attempts=attempts,
        )
    return Verdict(
        label="ran_after_repair",
        evidence="The commands exited 0 after one or more repairs.",
        attempts=attempts,
    )
