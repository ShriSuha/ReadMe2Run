from pathlib import Path

import yaml
from pydantic import BaseModel


class AppSettings(BaseModel):
    log_level: str
    runs_dir: str


class ModelSettings(BaseModel):
    model: str
    base_url: str
    num_ctx: int
    temperature: float


class SandboxSettings(BaseModel):
    command_timeout: int
    build_install_timeout: int
    memory: str
    nano_cpus: int
    images: dict[str, str]


class PoliciesSettings(BaseModel):
    max_repairs: int
    repo_size_cap_mb: int
    tree_cap_paths: int
    readme_cap_characters: int
    apt_allowlist: list[str]


class Settings(BaseModel):
    app: AppSettings
    model: ModelSettings
    sandbox: SandboxSettings
    policies: PoliciesSettings


def _config_dir() -> Path:
    """Find the project's configurations folder.

    This file lives at src/readme2run/configurations/loader.py.
    Going up three folders reaches the repository root, where the
    yaml files sit in configurations/.
    """
    return Path(__file__).resolve().parents[3] / "configurations"


def _read_yaml(path: Path) -> dict:
    """Read one yaml file and return its mapping.

    Comments in the file are ignored. A file that is not a mapping
    of names to values is rejected, because each settings group
    expects named fields.
    """
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a mapping")
    return data


def load_settings(config_dir: Path | None = None) -> Settings:
    """Load the four yaml files into one Settings object.

    Other parts of the program call this and then read fields such as
    settings.model.model. They do not open the yaml files themselves.
    Pass config_dir to load a different folder, for example in a test.
    """
    root = Path(config_dir) if config_dir is not None else _config_dir()
    return Settings(
        app=AppSettings.model_validate(_read_yaml(root / "app.yaml")),
        model=ModelSettings.model_validate(_read_yaml(root / "model.yaml")),
        sandbox=SandboxSettings.model_validate(_read_yaml(root / "sandbox.yaml")),
        policies=PoliciesSettings.model_validate(_read_yaml(root / "policies.yaml")),
    )
