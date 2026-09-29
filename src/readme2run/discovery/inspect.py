from pathlib import Path

from readme2run.configurations.loader import Settings, load_settings
from readme2run.discovery.blockers import find_blockers
from readme2run.discovery.ci import find_ci_commands
from readme2run.discovery.docker_file import find_dockerfile
from readme2run.discovery.make_file import find_makefile_targets
from readme2run.discovery.manifests import find_manifests
from readme2run.discovery.readme import read_readme
from readme2run.discovery.tree import list_tree
from readme2run.schemas.facts import RepoFacts


def _detect_languages(manifests: list[str], tree: list[str]) -> list[str]:
    languages: list[str] = []
    joined = set(manifests) | set(tree)
    if any(name in joined for name in ("requirements.txt", "pyproject.toml")) or any(
        p.endswith(".py") for p in tree
    ):
        languages.append("python")
    if "package.json" in joined:
        languages.append("node")
    if "go.mod" in joined or any(p.endswith(".go") for p in tree):
        languages.append("go")
    if "Cargo.toml" in joined:
        languages.append("rust")
    return languages


def inspect_repo(path: Path | str, settings: Settings | None = None) -> RepoFacts:
    """Compose RepoFacts from the checkout. No model is involved."""
    cfg = settings or load_settings()
    root = Path(path)
    tree = list_tree(root, cfg)
    readme = read_readme(root, cfg)
    manifests = find_manifests(root)
    return RepoFacts(
        readme=readme,
        tree=tree,
        manifests=manifests,
        dockerfile_path=find_dockerfile(root),
        makefile_targets=find_makefile_targets(root),
        ci_commands=find_ci_commands(root),
        languages=_detect_languages(manifests, tree),
        blockers=find_blockers(readme, tree),
    )
