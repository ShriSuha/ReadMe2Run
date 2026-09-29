from pathlib import Path

from readme2run.tools.crew_tools import (
    DirectoryTreeTool,
    DockerExecTool,
    all_crew_tools,
)
from readme2run.tools.git_clone import ToolRejected
from readme2run.tools.docker_exec import docker_exec
import pytest


def test_crew_tools_have_names_and_descriptions() -> None:
    tools = all_crew_tools()
    assert {t.name for t in tools} >= {
        "git_clone",
        "directory_tree",
        "read_file",
        "artifact_list",
        "docker_exec",
    }
    for tool in tools:
        assert tool.description


def test_directory_tree_tool_lists_main_py() -> None:
    result = DirectoryTreeTool()._run(str(Path("tests/fixtures/hello").resolve()))
    assert "main.py" in result


def test_docker_exec_tool_rejects_sudo() -> None:
    text = DockerExecTool()._run(container_id="none", script="sudo apt-get install git")
    assert text.startswith("rejected:")


def test_docker_exec_core_rejects_sudo_without_docker() -> None:
    with pytest.raises(ToolRejected):
        docker_exec("none", "sudo true", timeout_s=1)
