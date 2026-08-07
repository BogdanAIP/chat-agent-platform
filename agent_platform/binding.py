from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import load_yaml_compatible
from .errors import BindingError


@dataclass(frozen=True)
class ProjectBinding:
    project_id: str
    repo_root: Path
    local_root: Path
    artifact_root: Path
    policy_path: Path


def resolve_project(repo_root: Path, project_id: str | None) -> ProjectBinding:
    config_path = repo_root / "config" / "projects.yaml"
    config = load_yaml_compatible(config_path)
    projects = config.get("projects", [])
    selected_id = project_id or config.get("active_project_id")
    if not selected_id:
        raise BindingError("No project_id supplied and no active_project_id configured")

    matches = [item for item in projects if item.get("project_id") == selected_id]
    if len(matches) != 1:
        raise BindingError(
            f"Project binding must resolve exactly once: {selected_id!r}; matches={len(matches)}"
        )

    item = matches[0]
    config_dir = config_path.parent

    def resolve(value: str) -> Path:
        return (config_dir / value).resolve()

    bound_repo = resolve(item["repo_root"])
    local_root = resolve(item["local_root"])
    artifact_root = resolve(item["artifact_root"])
    policy_path = (config_dir / item["policy"]).resolve()
    if bound_repo != repo_root.resolve():
        raise BindingError(
            f"Binding repo_root {bound_repo} does not match active repository {repo_root.resolve()}"
        )
    artifact_root.mkdir(parents=True, exist_ok=True)
    return ProjectBinding(selected_id, bound_repo, local_root, artifact_root, policy_path)

