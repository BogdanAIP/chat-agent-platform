from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from runtime.agent_sessions import chatgpt_temporary, source_attestation
from runtime.control_plane.delegation_state import (
    DelegationStateError,
    WORKER_PROFILE,
    load_delegation,
    prepare_delegation,
)

from .independent_review_state import (
    ReviewIdentity,
    ReviewStateError,
    parse_review_result,
    prepare_review_operation,
    review_operation_key,
    submit_independent_review_result,
)


WORKER_KIND = "code-review"
RESULT_CONTRACT_ID = "review_result_v1"
_AUTOMATIC_REVIEW_WORKER_MODULE = "runtime.control_plane.automatic_review_worker"
_REPOSITORY = "BogdanAIP/chat-agent-platform"
_BRANCH = "main"
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
_GENERATION_RE = re.compile(
    r'CAPChatGPTTemporaryExecutionGeneration\s*=\s*"([0-9a-f]{64})"'
)
_UPDATE_STATE_KEYS = {
    "schema_version",
    "repository",
    "branch",
    "installed_commit_sha",
    "installed_at",
    "status",
    "target_commit_sha",
    "last_checked_at",
    "last_error",
}


def build_review_worker_task(identity: ReviewIdentity, *, review_run_id: str) -> str:
    """Build the exact specialist task carried inside generic WORKER_TASK_V1."""

    return f"""REVIEW_REQUEST_V1
repository={identity.repository}
pr_number={identity.pr_number}
base_sha={identity.base_sha}
head_sha={identity.head_sha}
review_skill={identity.review_skill}
review_skill_version={identity.review_skill_version}
review_run_id={review_run_id}

Perform the mandatory independent semantic code review for exactly BASE_SHA..HEAD_SHA.

Read the governing AGENTS.md and .agents/skills/code-review/SKILL.md from BASE_SHA.
Enumerate the repository skills at HEAD_SHA and apply every target-specific skill whose trigger matches the reviewed change.
Reconstruct the PR/diff/tests/evidence independently from read-only public repository evidence.
Do not use apps, plugins or connectors and do not mutate GitHub or any external state.

Return the complete automatic REVIEW_RESULT_V1 text as your task-specific result payload.
The REVIEW_RESULT_V1 must remain bound to the exact repository, PR, BASE_SHA, HEAD_SHA,
review skill/version and review_run_id above. If the required evidence cannot be obtained
read-only, return a non-completing ABSTAIN result rather than guessing.
""".strip()


def review_delegation_identity(
    identity: ReviewIdentity,
    *,
    review_run_id: str,
) -> tuple[str, dict[str, str]]:
    task = build_review_worker_task(identity, review_run_id=review_run_id)
    operation_key = review_operation_key(identity)
    return task, {
        "parent_task_id": f"review-{operation_key[:48]}",
        "subgoal_id": f"pr-{identity.pr_number}-{identity.head_sha[:12]}",
        "worker_kind": WORKER_KIND,
        "worker_profile": WORKER_PROFILE,
        "task_sha256": chatgpt_temporary.task_sha256(task),
        "result_contract_id": RESULT_CONTRACT_ID,
    }


def prepare_review_delegation(
    identity: ReviewIdentity,
    *,
    review_run_id: str,
    delegation_state_root: Path,
) -> tuple[str, dict[str, str]]:
    task, delegation_identity = review_delegation_identity(
        identity,
        review_run_id=review_run_id,
    )
    prepare_delegation(delegation_identity, state_root=delegation_state_root)
    return task, delegation_identity


def settle_review_from_delegation(
    identity_value: Mapping[str, Any],
    *,
    reviewer_state_root: Path,
    delegation_state_root: Path,
) -> dict[str, Any] | None:
    """Commit an already-recorded generic worker result into reviewer state.

    This function never creates launch or Send authority. It is settlement-only.
    """

    prepared_review = prepare_review_operation(identity_value, state_root=reviewer_state_root)
    task, delegation_identity = review_delegation_identity(
        prepared_review.identity,
        review_run_id=prepared_review.review_run_id,
    )
    del task

    try:
        snapshot = load_delegation(delegation_identity, state_root=delegation_state_root)
    except DelegationStateError as exc:
        # A reviewer operation may legitimately predate Delegation migration or
        # may still be prepared before the generic child state has been created.
        if "does not exist" in str(exc):
            return None
        raise ReviewStateError(f"delegated reviewer state is invalid: {exc}") from exc

    if snapshot.result_state != "recorded":
        return None

    if snapshot.result_status != "COMPLETED":
        return {
            "schema_version": 1,
            "status": "worker_terminal_noncompleting",
            "worker_status": snapshot.result_status,
            "delegation_id": snapshot.delegation_id,
            "result_sha256": snapshot.result_sha256,
        }

    payload = snapshot.result_payload
    if type(payload) is not str or not payload:
        raise ReviewStateError("delegated reviewer completed without a bounded result payload")

    parsed = parse_review_result(
        payload,
        expected_identity=prepared_review.identity,
        automatic=True,
        expected_review_run_id=prepared_review.review_run_id,
    )
    if (
        parsed.header["status"] not in {"PASS", "FINDINGS"}
        or parsed.header["review_validity"] != "CURRENT"
    ):
        return {
            "schema_version": 1,
            "status": "review_terminal_noncompleting",
            "review_status": parsed.header["status"],
            "review_validity": parsed.header["review_validity"],
            "delegation_id": snapshot.delegation_id,
            "result_sha256": snapshot.result_sha256,
        }

    try:
        settled = submit_independent_review_result(
            {
                "review_run_id": prepared_review.review_run_id,
                "result": payload,
            },
            state_root=reviewer_state_root,
        )
    except ReviewStateError:
        # Preserve reviewer-specific race semantics. A manual fallback that
        # committed first remains authoritative; malformed/stale automatic
        # payloads remain fail-closed and are surfaced to the caller.
        raise

    return {
        **settled,
        "delegation_id": snapshot.delegation_id,
        "delegation_result_sha256": snapshot.result_sha256,
    }


def review_delegation_state_root() -> Path:
    """Return the accepted private state root for generic Agent Sessions."""

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise ReviewStateError("LOCALAPPDATA is required for automatic reviewer delegation")
    return (
        Path(local_app_data)
        / "ChatAgentPlatform"
        / "agent-sessions"
        / "private-state"
    ).resolve()


def _installed_app_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise ReviewStateError("LOCALAPPDATA is required for automatic reviewer launch")
    root = (Path(local_app_data) / "ChatAgentPlatform" / "app").resolve()
    if not root.is_dir():
        raise ReviewStateError("installed Chat Agent Platform app root is unavailable")
    return root


def _installed_review_head(local_root: Path) -> str:
    update_path = local_root / "state" / "platform-update.json"
    try:
        raw = update_path.read_bytes()
    except OSError as exc:
        raise ReviewStateError("installed-version state is unavailable") from exc
    if not raw or len(raw) > 64_000:
        raise ReviewStateError("installed-version state has invalid size")
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewStateError("installed-version state is invalid JSON") from exc
    if type(value) is not dict or set(value) != _UPDATE_STATE_KEYS:
        raise ReviewStateError("installed-version state keys mismatch")
    if value["schema_version"] != 1:
        raise ReviewStateError("installed-version state schema mismatch")
    if value["repository"] != _REPOSITORY or value["branch"] != _BRANCH:
        raise ReviewStateError("installed-version source identity mismatch")
    if value["status"] not in {"current", "update_available"}:
        raise ReviewStateError("installed runtime is not in a reviewer-safe update state")
    head = value["installed_commit_sha"]
    if type(head) is not str or _HEX40_RE.fullmatch(head) is None:
        raise ReviewStateError("installed runtime has no exact accepted-main identity")
    return head


def validate_review_worker_runtime(*, state_root: Path) -> tuple[Path, str]:
    """Prove the fixed installed reviewer runtime before dispatch is consumed."""

    if os.name != "nt":
        raise ReviewStateError("automatic reviewer launch is supported only on Windows")

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise ReviewStateError("LOCALAPPDATA is required for automatic reviewer launch")
    local_root = (Path(local_app_data) / "ChatAgentPlatform").resolve()
    expected_state_root = (local_root / "state").resolve()
    resolved_state_root = state_root.resolve()
    if (
        resolved_state_root != expected_state_root
        and not resolved_state_root.is_relative_to(expected_state_root)
    ):
        raise ReviewStateError("automatic reviewer requires the installed CAP private state root")

    app_root = _installed_app_root()
    expected_head = _installed_review_head(local_root)

    required = (
        app_root / "runtime" / "control_plane" / "automatic_review_worker.py",
        app_root / "runtime" / "control_plane" / "independent_review_delegation.py",
        app_root / "runtime" / "control_plane" / "delegation_state.py",
        app_root / "runtime" / "agent_sessions" / "chatgpt_temporary.py",
        app_root / "runtime" / "agent_sessions" / "chatgpt_temporary_controller.py",
        app_root / "runtime" / "agent_sessions" / "chatgpt_temporary_authenticated_controller.py",
        app_root / "runtime" / "agent_sessions" / "source_attestation.py",
    )
    for path in required:
        if not path.is_file():
            raise ReviewStateError(f"installed automatic reviewer runtime asset is missing: {path.name}")

    extension_root = (
        app_root / "runtime" / "agent_sessions" / "chatgpt_temporary_extension"
    )
    for name in source_attestation.RUNTIME_ASSETS:
        if not (extension_root / name).is_file():
            raise ReviewStateError(
                f"installed reviewer extension asset is missing: {name}"
            )
    try:
        generation_text = (extension_root / "execution_generation.js").read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        raise ReviewStateError(
            "installed reviewer execution generation is unavailable"
        ) from exc
    if _GENERATION_RE.search(generation_text) is None:
        raise ReviewStateError("installed reviewer execution generation is invalid")

    return app_root, expected_head


def spawn_review_worker(
    identity: ReviewIdentity,
    *,
    state_root: Path,
) -> None:
    """Start exactly one fixed reviewer-owned worker process.

    Reviewer dispatch must already be durably marked before this is called.
    The child owns its bounded controller/browser lifetime and is never
    automatically relaunched by this function.
    """

    app_root, _expected_head = validate_review_worker_runtime(state_root=state_root)
    del _expected_head

    bootstrap = (
        "import runpy,sys;"
        "root=sys.argv.pop(1);"
        "sys.path.insert(0,root);"
        f'runpy.run_module("{_AUTOMATIC_REVIEW_WORKER_MODULE}",run_name="__main__")'
    )
    command = [
        sys.executable,
        "-I",
        "-B",
        "-S",
        "-c",
        bootstrap,
        str(app_root),
        "--repository",
        identity.repository,
        "--pr-number",
        str(identity.pr_number),
        "--base-sha",
        identity.base_sha,
        "--head-sha",
        identity.head_sha,
        "--review-skill",
        identity.review_skill,
        "--review-skill-version",
        identity.review_skill_version,
        "--state-root",
        str(state_root.resolve()),
    ]

    creationflags = 0
    creationflags |= int(getattr(subprocess, "DETACHED_PROCESS", 0))
    creationflags |= int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))

    try:
        subprocess.Popen(
            command,
            cwd=str(app_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creationflags,
        )
    except OSError as exc:
        raise ReviewStateError(f"automatic reviewer worker spawn failed: {type(exc).__name__}") from exc
