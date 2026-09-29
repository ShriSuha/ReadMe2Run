"""CrewAI tool wrappers around the plain Python tool cores.

Agents call these. Guardrails stay inside the cores.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from readme2run.tools import artifact_list as artifact_list_core
from readme2run.tools import directory_tree as directory_tree_core
from readme2run.tools import docker_exec as docker_exec_core
from readme2run.tools import read_file as read_file_core
from readme2run.tools.git_clone import CloneRequest, GitCloneTool, ToolRejected


class DirectoryTreeInput(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the cloned repository")


class DirectoryTreeTool(BaseTool):
    name: str = "directory_tree"
    description: str = "List relative file paths in the repository checkout."
    args_schema: Type[BaseModel] = DirectoryTreeInput

    def _run(self, repo_path: str) -> str:
        try:
            return json.dumps(directory_tree_core.directory_tree(repo_path))
        except ToolRejected as exc:
            return f"rejected: {exc.reason}"


class ReadFileInput(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the cloned repository")
    relative_path: str = Field(..., description="File path relative to the repo root")


class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "Read one text file from the repository checkout."
    args_schema: Type[BaseModel] = ReadFileInput

    def _run(self, repo_path: str, relative_path: str) -> str:
        try:
            return read_file_core.read_file(repo_path, relative_path)
        except ToolRejected as exc:
            return f"rejected: {exc.reason}"


class ArtifactListInput(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the cloned repository")
    expected: list[str] = Field(..., description="Relative paths to check for existence")


class ArtifactListTool(BaseTool):
    name: str = "artifact_list"
    description: str = "Check which expected artifact paths already exist in the repo."
    args_schema: Type[BaseModel] = ArtifactListInput

    def _run(self, repo_path: str, expected: list[str]) -> str:
        try:
            return json.dumps(artifact_list_core.artifact_list(repo_path, expected))
        except ToolRejected as exc:
            return f"rejected: {exc.reason}"


class DockerExecInput(BaseModel):
    container_id: str = Field(..., description="Running sandbox container id")
    script: str = Field(..., description="Shell command to run inside /work")
    timeout_s: int = Field(300, description="Seconds before the command is killed")
    phase: str = Field("run", description="setup or run")


class DockerExecTool(BaseTool):
    name: str = "docker_exec"
    description: str = (
        "Run one shell command inside the sandbox container. "
        "Unsafe commands such as sudo are rejected."
    )
    args_schema: Type[BaseModel] = DockerExecInput

    def _run(
        self,
        container_id: str,
        script: str,
        timeout_s: int = 300,
        phase: str = "run",
    ) -> str:
        try:
            attempt = docker_exec_core.docker_exec(
                container_id, script, timeout_s=timeout_s, phase=phase
            )
        except ToolRejected as exc:
            return f"rejected: {exc.reason}"
        return attempt.model_dump_json()


class GitCloneInput(BaseModel):
    url: str = Field(..., description="Repository URL to clone")
    run_dir_repo: str = Field(..., description="Destination checkout path (RunDir.repo)")
    allow_file_urls: bool = Field(False, description="Allow file:// URLs for tests")


class GitCloneCrewTool(BaseTool):
    name: str = "git_clone"
    description: str = "Clone a repository into the run folder after URL policy checks."
    args_schema: Type[BaseModel] = GitCloneInput

    def _run(self, url: str, run_dir_repo: str, allow_file_urls: bool = False) -> str:
        from readme2run.configurations.loader import load_settings
        from readme2run.workspace.run_dir import RunDir

        settings = load_settings().model_copy(update={"allow_file_urls": allow_file_urls})
        run_dir = RunDir(
            path=Path(run_dir_repo).parent,
            repo=Path(run_dir_repo),
            logs=Path(run_dir_repo).parent / "logs",
            events_path=Path(run_dir_repo).parent / "events.jsonl",
        )
        try:
            result = GitCloneTool().run(
                CloneRequest(url=url, run_dir=run_dir, settings=settings)
            )
        except ToolRejected as exc:
            return f"rejected: {exc.reason}"
        return str(result.path)


def all_crew_tools() -> list[BaseTool]:
    """Return the standard tool set for agents."""
    return [
        GitCloneCrewTool(),
        DirectoryTreeTool(),
        ReadFileTool(),
        ArtifactListTool(),
        DockerExecTool(),
    ]
