"""Build the CrewAI LLM client from model.yaml."""

from crewai import LLM

from readme2run.configurations.loader import Settings, load_settings


def build_llm(settings: Settings | None = None) -> LLM:
    """Return a CrewAI LLM pointed at the local Ollama server."""
    cfg = settings or load_settings()
    return LLM(
        model=f"ollama/{cfg.model.model}",
        base_url=cfg.model.base_url,
        temperature=cfg.model.temperature,
        # num_ctx is passed through to the provider when supported.
        extra_body={"options": {"num_ctx": cfg.model.num_ctx}},
    )
