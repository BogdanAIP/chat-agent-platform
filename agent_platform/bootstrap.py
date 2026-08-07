from __future__ import annotations

import json
from pathlib import Path

from .binding import resolve_project
from .config import load_yaml_compatible
from .errors import ValidationError


MINIMAL_CONTEXT = ("CURRENT_STATE.md", "ARCHITECTURE.md", "CONSTRAINTS.md")


def build_bootstrap_context(
    repo_root: Path, *, project_id: str | None, capability: str
) -> dict:
    binding = resolve_project(repo_root, project_id)
    requirements = load_yaml_compatible(repo_root / "config" / "capability-requirements.yaml")
    matches = [
        item for item in requirements.get("requirements", []) if item.get("capability") == capability
    ]
    if len(matches) != 1:
        raise ValidationError(
            f"Capability requirement must resolve exactly once: {capability!r}; matches={len(matches)}"
        )

    context = {}
    for filename in MINIMAL_CONTEXT:
        path = repo_root / "project-context" / filename
        try:
            context[filename] = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValidationError(f"Required bootstrap context is unavailable: {path}") from exc

    runtime_slice = {"status": "unknown", "reason": "runtime profile has not been generated"}
    profile_path = repo_root / "runtime" / "capability-profile.json"
    if profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError("Runtime capability profile is corrupt") from exc
        if profile.get("project_id") != binding.project_id:
            runtime_slice = {"status": "unknown", "reason": "runtime profile belongs to another project"}
        else:
            runtime_slice = profile.get("capabilities", {}).get(
                capability, {"status": "unknown", "reason": "capability has not been probed"}
            )

    skill_path = repo_root / "project-skills" / _skill_for(capability) / "SKILL.md"
    return {
        "contract_version": "bootstrap-v1",
        "project": {
            "project_id": binding.project_id,
            "repo_root": str(binding.repo_root),
            "artifact_root": str(binding.artifact_root),
        },
        "capability_requirement": matches[0],
        "runtime_capability": runtime_slice,
        "minimal_context": context,
        "relevant_skill": str(skill_path) if skill_path.exists() else None,
    }


def _skill_for(capability: str) -> str:
    return "media-inspection" if capability == "media.inspect" else capability.replace(".", "-")
