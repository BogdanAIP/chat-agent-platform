from __future__ import annotations

import platform
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .artifacts import ArtifactStore
from .binding import resolve_project
from .contracts import validate_contract
from .media import inspect_media, tool_versions
from .policy import PolicyEnforcementPoint


def inspect_file(
    repo_root: Path,
    file_path: Path,
    *,
    project_id: str | None,
    data_class: str = "project",
    requested_risk_hint: str | None = None,
) -> dict:
    request_id = f"req_{uuid4().hex}"
    request = {
        "contract_version": "tool-v1",
        "request_id": request_id,
        "capability": "media.inspect",
        "idempotency_key": None,
        "requested_risk_hint": requested_risk_hint,
        "cost_limit": 0,
        "artifact_refs": [],
        "parameters": {"source_name": file_path.name, "data_class": data_class},
    }
    validate_contract(request, "tool-request-v1.schema.json")
    binding = resolve_project(repo_root, project_id)
    policy = PolicyEnforcementPoint(binding.policy_path).evaluate(
        "media.inspect",
        parameters={"source_name": file_path.name},
        data_class=data_class,
        requested_risk_hint=requested_risk_hint,
    )
    store = ArtifactStore(binding.artifact_root)
    artifact = store.import_file(file_path, created_by="media.inspect", data_class=data_class)
    analysis = inspect_media(Path(artifact.path))
    store.update_metadata(artifact, analysis)
    result = {
        "request_id": request_id,
        "status": "success",
        "result": analysis,
        "artifact_refs": [
            {
                "artifact_id": artifact.artifact_id,
                "sha256": artifact.sha256,
                "data_class": artifact.data_class,
            }
        ],
        "provenance": {
            "capability": "media.inspect",
            "executor": "local.ffmpeg",
            "project_id": binding.project_id,
            "validated": True,
        },
        "policy_decision_id": policy.decision_id,
        "error": None,
    }
    validate_contract(result, "tool-v1.schema.json")
    validate_contract(asdict(policy), "policy-decision-v1.schema.json")
    return result


def build_runtime_profile(repo_root: Path, project_id: str | None) -> dict:
    binding = resolve_project(repo_root, project_id)
    tools = tool_versions()
    available = all(tools[name]["available"] for name in ("ffmpeg", "ffprobe"))
    return {
        "contract_version": "runtime-capability-profile-v1",
        "verified_at": datetime.now(UTC).isoformat(),
        "surface": "local_windows",
        "project_id": binding.project_id,
        "system": platform.platform(),
        "python": platform.python_version(),
        "capabilities": {
            "media.inspect": {
                "status": "available" if available else "unavailable",
                "execution_path": "local.ffmpeg",
                "tools": tools,
            }
        },
        "binding": {
            "repo_root": str(binding.repo_root),
            "local_root": str(binding.local_root),
            "artifact_root": str(binding.artifact_root),
        },
    }
