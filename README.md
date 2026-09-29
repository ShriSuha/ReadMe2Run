# ReadMe2Run

ReadMe2Run reads a repository README, plans how to run it, executes that plan in a Docker sandbox, and writes a verdict.

It is an **agentic** system built with CrewAI. Four agents can take part:

- **Inspector** — explores the repo with `directory_tree` and `read_file`
- **Architect** — proposes a `RunPlan` (with tools if needed)
- **Driver** — runs and repairs commands with `docker_exec`
- **Analyst** — writes the human-readable evidence paragraph

Every tool runs a **guardrail** first. Unsafe URLs and commands are rejected.

Deterministic discovery and planning remain as fallbacks when an agent fails.

## Requirements

- Python 3.11+
- Docker
- Ollama with model `qwen2.5:14b` (for `--agents`)

## Install

```bash
uv sync
```

## Commands

```bash
# Run a public repo
uv run readme2run run https://github.com/org/repo

# Run a local fixture (tests)
uv run readme2run run --allow-file-urls file:///absolute/path/to/tests/fixtures/hello

# Use CrewAI agents
uv run readme2run run --agents --allow-file-urls file:///absolute/path/to/tests/fixtures/hello

# List past runs
uv run readme2run runs

# Show one run
uv run readme2run show <run-id>
```

Runs are stored under `~/.local/share/readme2run/runs/<run-id>/`.

## Model

Agents use `qwen2.5:14b` through Ollama at `http://127.0.0.1:11434`.

## Verdict labels

- `ran_as_documented` — documented commands exited 0 with no repairs
- `ran_after_repair` — exited 0 after repairs
- `blocked_missing_secret` — needs a secret this tool does not have
- `blocked_needs_gpu_or_data` — needs GPU or data this sandbox cannot provide
- `readme_insufficient` — no run command found in README or CI
- `failed` — still non-zero after allowed repairs

## Supported stacks

Dockerfile, Python, Node, Go, Rust. Makefile targets and GitHub Actions `run:` steps can supply commands.

## Safety

- Repairs may add a setup command or environment variable
- Only allowlisted apt packages may be installed
- Project source files are never edited
- GPU jobs, notebooks, private repos, and Compose are outside this version
