# ReadMe2Run

ReadMe2Run turns a repository README into a real run.

Given a public GitHub URL, it:

1. Clones the repo
2. Reads the README and project files
3. Builds a plan to install and run it
4. Executes that plan inside a Docker sandbox
5. Writes a verdict and a report

It is an **agentic** system built with [CrewAI](https://www.crewai.com/). Four agents can take part:

| Agent | Role | Tools |
|---|---|---|
| **Inspector** | Explore the checkout and fill repo facts | `directory_tree`, `read_file` |
| **Architect** | Propose a `RunPlan` | `directory_tree`, `read_file` |
| **Driver** | Run and repair commands in the sandbox | `docker_exec` |
| **Analyst** | Write the evidence paragraph a person reads | (no Docker tools) |

Agent roles and tasks live in YAML (`src/readme2run/agents/config/`). `crew.py` wires them to tools and the local LLM — the same beginner pattern as a typical CrewAI tutorial.
Every tool runs a **guardrail** first. Unsafe URLs and commands are rejected even if an agent asks for them.

Without `--agents`, ReadMe2Run still works using deterministic discovery and planning. Those paths also act as fallbacks when an agent fails.

## Requirements

- Python **3.11+**
- [uv](https://docs.astral.sh/uv/)
- Docker running (`docker info` should succeed)
- For `--agents`: [Ollama](https://ollama.com/) with model **`qwen2.5:14b`**

```bash
# optional, only if you use --agents
ollama pull qwen2.5:14b
```

## Install

```bash
git clone https://github.com/ShriSuha/ReadMe2Run.git
cd ReadMe2Run
uv sync
```

## Quick start (hello fixture)

This is the smallest end-to-end check. No agents required.

```bash
cd ReadMe2Run
uv run readme2run run --allow-file-urls "file://$(pwd)/tests/fixtures/hello"
```

You should see live phases and commands, then a verdict of `ran_as_documented` and output containing `hello-readme2run`.

## Commands

### Run a public repository

```bash
uv run readme2run run https://github.com/org/repo
```

Use an `https://` URL. `ssh://` and other schemes are rejected.

### Run with CrewAI agents

```bash
uv run readme2run run --agents https://github.com/org/repo
```

Needs Ollama serving `qwen2.5:14b` at `http://127.0.0.1:11434`.

### List past runs

```bash
uv run readme2run runs
```

### Show one run

```bash
uv run readme2run show <run-id>
```

Prints the verdict and replays `events.jsonl`.

## Where runs are stored

Each run lives under:

```text
~/.local/share/readme2run/runs/<timestamp>-<slug>/
  repo/           cloned project
  logs/
  events.jsonl    live event stream
  report.md       human-readable report
  report.json     full RunState
```

## Model

Agents use **`qwen2.5:14b`** through Ollama (`http://127.0.0.1:11434`). Settings live in `configurations/model.yaml`.

## Verdict labels

| Label | Meaning |
|---|---|
| `ran_as_documented` | Documented commands exited 0 with no repairs |
| `ran_after_repair` | Exited 0 after one or more repairs |
| `blocked_missing_secret` | Needs a secret this tool does not have |
| `blocked_needs_gpu_or_data` | Needs a GPU or data this sandbox cannot provide |
| `readme_insufficient` | No run command found in the README or CI |
| `failed` | Still non-zero after the allowed repairs |

## Supported stacks

- Dockerfile (preferred when present)
- Python (`requirements.txt`, Poetry, uv)
- Node (`npm` / `pnpm` / `yarn` lockfiles)
- Go
- Rust
- Makefile targets and GitHub Actions `run:` steps as command sources

## Safety

- Agents may only act through tools in `src/readme2run/tools/`
- Every tool calls a guardrail before doing work
- Repairs may add a setup command or an environment variable
- Only allowlisted apt packages may be installed (`configurations/policies.yaml`)
- Project source files are never edited
- Host environment variables are not copied into the container

## Out of scope (this version)

- GPU jobs
- Notebooks as the primary entrypoint
- Private repositories
- Docker Compose multi-service apps

## Project layout (short)

```text
configurations/          yaml settings (app, model, sandbox, policies)
src/readme2run/
  agents/
    config/agents.yaml   # who the agents are (edit here)
    config/tasks.yaml    # what each task asks for (edit here)
    crew.py              # wires agents, tasks, tools, LLM
    llm.py               # builds the Ollama model client
  discovery/             deterministic RepoFacts (fallback)
  planning/              deterministic RunPlan (fallback)
  tools/                 guarded actions + CrewAI wrappers
  sandbox/               Docker start / stop / exec
  orchestration/         Flow, events, repair loop
  guardrails/            URL, command, repair, resource, secrets
  cli/                   readme2run entrypoint
tests/fixtures/hello/    smallest working example
```

Agents follow the usual CrewAI beginner pattern: change behaviour in YAML, wire tools in `crew.py`.
## Tests

```bash
uv run pytest -q
```

## License

See [LICENSE](LICENSE).
