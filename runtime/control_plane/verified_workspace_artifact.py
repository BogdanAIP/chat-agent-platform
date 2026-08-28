from __future__ import annotations

import secrets
import time
from pathlib import Path
from typing import Any, Callable

from ._verified_workspace_artifact_support import (
    CHECKPOINT_SCHEMA_VERSION,
    MAX_ACTIONS,
    MAX_CONTENT_BYTES,
    MAX_CONTENT_CHARS,
    MAX_RUNTIME_SECONDS,
    PROCEDURE_ID,
    PROCEDURE_STATUS,
    PROCEDURE_VERSION,
    QUALIFICATION_ADMISSION,
    RESERVED_WORKSPACE_DIR,
    _ARTIFACT_RE,
    _RESUMABLE_NODES,
    _TASK_ID_RE,
    _WORKSPACE_GUARD,
    _acquire_task_lock,
    _advance_working_observation,
    _commit_recovered_applied_transition,
    _evidence,
    _exclusive_create_file,
    _exclusive_link_file,
    _file_identity,
    _file_predicates,
    _intent_from_marker,
    _is_missing,
    _kernel_receipt,
    _load_checkpoint,
    _matches_expected_file,
    _missing_predicates,
    _new_working_state,
    _normalized_identity,
    _observed_evidence,
    _observed_identity,
    _prepare_transition,
    _record_file_exists_no_effect,
    _record_normal_outcome,
    _record_transition,
    _restore_working_state,
    _result,
    _rollback_owned_file,
    _safe_child,
    _same_file_identity,
    _same_node_applied_operation,
    _sha256,
    _unknown_failure,
    _utc_now,
    _validate_resume_state,
    _verify_current_state,
    _verify_from_intent,
    _verify_transition,
    _write_checkpoint,
)
from .file_artifact_observation import FileArtifactObservationStream
from .verification import (
    FinishStatus,
    ObservationSnapshot,
    VerificationResult,
    VerificationStatus,
    evaluate_finish_gate,
)
from .windows_file_pin import pin_file_for_verified_link
from .working_state import (
    AttemptIntent,
    MutatingOutcome,
    ReconciliationStatus,
    WorkingState,
    reconciliation_effect_id,
)


def _direct_reconciliation_status(
    transition_id: str,
    snapshot: ObservationSnapshot,
    *,
    content_size: int,
    expected_sha: str,
    staging_identity: dict[str, Any] | None,
    target_identity: dict[str, Any] | None = None,
) -> ReconciliationStatus:
    """Classify the fresh physical state without conflating path identities.

    Schema-1 final creation copied bytes, so a migrated staging path and target
    path can legitimately have different identities.  Schema-2 final creation
    hard-links the verified staging object, so the target must match the staging
    identity for that transition.  Cleanup must always validate each path against
    its own recorded identity.
    """

    if transition_id == "stage_create":
        if _matches_expected_file(
            snapshot,
            "staging",
            size=content_size,
            sha256=expected_sha,
        ):
            return ReconciliationStatus.CONFIRMED_APPLIED
        if _is_missing(snapshot, "staging") and _is_missing(snapshot, "target"):
            return ReconciliationStatus.CONFIRMED_NOT_APPLIED
        return ReconciliationStatus.STILL_UNKNOWN

    if transition_id == "final_create":
        if staging_identity is None:
            return ReconciliationStatus.STILL_UNKNOWN
        staging_ok = _matches_expected_file(
            snapshot,
            "staging",
            size=content_size,
            sha256=expected_sha,
            identity=staging_identity,
        )
        if staging_ok and _matches_expected_file(
            snapshot,
            "target",
            size=content_size,
            sha256=expected_sha,
            identity=staging_identity,
        ):
            return ReconciliationStatus.CONFIRMED_APPLIED
        if staging_ok and _is_missing(snapshot, "target"):
            return ReconciliationStatus.CONFIRMED_NOT_APPLIED
        return ReconciliationStatus.STILL_UNKNOWN

    if transition_id == "staging_cleanup":
        if staging_identity is None or target_identity is None:
            return ReconciliationStatus.STILL_UNKNOWN
        target_ok = _matches_expected_file(
            snapshot,
            "target",
            size=content_size,
            sha256=expected_sha,
            identity=target_identity,
        )
        if target_ok and _is_missing(snapshot, "staging"):
            return ReconciliationStatus.CONFIRMED_APPLIED
        if target_ok and _matches_expected_file(
            snapshot,
            "staging",
            size=content_size,
            sha256=expected_sha,
            identity=staging_identity,
        ):
            return ReconciliationStatus.CONFIRMED_NOT_APPLIED
        return ReconciliationStatus.STILL_UNKNOWN

    raise ValueError("unknown workspace transition")


def _reconciliation_predicates(
    transition_id: str,
    status: ReconciliationStatus,
    snapshot: ObservationSnapshot,
    *,
    content_size: int,
    expected_sha: str,
    staging_identity: dict[str, Any] | None,
    target_identity: dict[str, Any] | None,
) -> tuple | None:
    """Return the exact kernel predicates required to confirm reconciliation."""

    staging_identity = _normalized_identity(staging_identity)
    target_identity = _normalized_identity(target_identity)

    if transition_id == "stage_create":
        if status is ReconciliationStatus.CONFIRMED_APPLIED:
            observed_identity = _observed_identity(snapshot, "staging")
            if observed_identity is None:
                return None
            return (
                *_file_predicates(
                    "staging",
                    size=content_size,
                    sha256=expected_sha,
                    identity=observed_identity,
                ),
                *_missing_predicates("target"),
            )
        if status is ReconciliationStatus.CONFIRMED_NOT_APPLIED:
            return (*_missing_predicates("staging"), *_missing_predicates("target"))
        return None

    if transition_id == "final_create":
        if staging_identity is None:
            return None
        if status is ReconciliationStatus.CONFIRMED_APPLIED:
            return (
                *_file_predicates(
                    "staging",
                    size=content_size,
                    sha256=expected_sha,
                    identity=staging_identity,
                ),
                *_file_predicates(
                    "target",
                    size=content_size,
                    sha256=expected_sha,
                    identity=staging_identity,
                ),
            )
        if status is ReconciliationStatus.CONFIRMED_NOT_APPLIED:
            return (
                *_file_predicates(
                    "staging",
                    size=content_size,
                    sha256=expected_sha,
                    identity=staging_identity,
                ),
                *_missing_predicates("target"),
            )
        return None

    if transition_id == "staging_cleanup":
        if staging_identity is None or target_identity is None:
            return None
        target_predicates = _file_predicates(
            "target",
            size=content_size,
            sha256=expected_sha,
            identity=target_identity,
        )
        if status is ReconciliationStatus.CONFIRMED_APPLIED:
            return (*target_predicates, *_missing_predicates("staging"))
        if status is ReconciliationStatus.CONFIRMED_NOT_APPLIED:
            return (
                *target_predicates,
                *_file_predicates(
                    "staging",
                    size=content_size,
                    sha256=expected_sha,
                    identity=staging_identity,
                ),
            )
        return None

    raise ValueError("unknown workspace transition")


def _kernel_reconciliation_verification(
    attempt_revision: int,
    intent: AttemptIntent,
    transition_id: str,
    direct_status: ReconciliationStatus,
    snapshot: ObservationSnapshot,
    *,
    task_id: str,
    content_size: int,
    expected_sha: str,
    staging_identity: dict[str, Any] | None,
    target_identity: dict[str, Any] | None,
) -> tuple[ReconciliationStatus, VerificationResult]:
    """Require the shared Verification Kernel before a confirmed reconciliation."""

    evidence_batch_id = f"{task_id}:reconcile:{attempt_revision}:{snapshot.ref.sequence}"
    if direct_status is ReconciliationStatus.STILL_UNKNOWN:
        return direct_status, VerificationResult(
            effect_id=reconciliation_effect_id(
                intent.operation_id,
                attempt_revision,
                ReconciliationStatus.STILL_UNKNOWN,
            ),
            status=VerificationStatus.UNKNOWN,
            reason="workspace_artifact_reconciliation_unknown",
            observation=snapshot.ref,
            evidence_batch_id=evidence_batch_id,
        )

    predicates = _reconciliation_predicates(
        transition_id,
        direct_status,
        snapshot,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=staging_identity,
        target_identity=target_identity,
    )
    if predicates is not None:
        result = _verify_from_intent(
            effect_id=reconciliation_effect_id(
                intent.operation_id,
                attempt_revision,
                direct_status,
            ),
            intent=intent,
            after=snapshot,
            predicates=predicates,
            evidence_batch_id=evidence_batch_id,
        )
        if result.status is VerificationStatus.PASS:
            return direct_status, result
        predicate_results = result.predicate_results
        reason = f"workspace_artifact_reconciliation_kernel_{result.status.value}"
    else:
        predicate_results = ()
        reason = "workspace_artifact_reconciliation_kernel_predicates_unavailable"

    return ReconciliationStatus.STILL_UNKNOWN, VerificationResult(
        effect_id=reconciliation_effect_id(
            intent.operation_id,
            attempt_revision,
            ReconciliationStatus.STILL_UNKNOWN,
        ),
        status=VerificationStatus.UNKNOWN,
        reason=reason,
        observation=snapshot.ref,
        evidence_batch_id=evidence_batch_id,
        predicate_results=predicate_results,
    )


def _authoritative_normal_status(
    direct_status: ReconciliationStatus,
    *,
    kernel_pass: bool,
) -> ReconciliationStatus:
    """Only shared-kernel success may turn a normal delivery into verified-applied state."""

    if direct_status is ReconciliationStatus.CONFIRMED_APPLIED and kernel_pass:
        return ReconciliationStatus.CONFIRMED_APPLIED
    return ReconciliationStatus.STILL_UNKNOWN


def _legacy_identity_generation_proven(value: Any) -> bool:
    """Historical schema-1 device/inode alone cannot exclude file-ID ABA reuse."""

    identity = _normalized_identity(value)
    return identity is not None and "birthtime_ns" in identity


def _recover_prepared_intent(
    task_state: dict[str, Any],
    state: WorkingState,
    observer: FileArtifactObservationStream,
    *,
    task_id: str,
    relative_target: str,
    expected_sha: str,
    content_size: int,
    checkpoint: Callable[[], None],
) -> tuple[WorkingState, dict[str, Any] | None, ObservationSnapshot | None]:
    marker = task_state.get("prepared_intent")
    if marker is None:
        return state, None, None
    if not isinstance(marker, dict):
        raise ValueError("prepared_intent is invalid")

    transition_id, intent = _intent_from_marker(
        marker,
        state,
        task_id=task_id,
        relative_target=relative_target,
        expected_sha=expected_sha,
        content_size=content_size,
        action_count=int(task_state["action_count"]),
    )
    state = state.record_attempt(
        intent,
        MutatingOutcome.OUTCOME_UNKNOWN,
        _unknown_failure(intent),
        expected_revision=state.revision,
        guard=_WORKSPACE_GUARD,
    )
    attempt = state.attempts[-1]
    fresh = observer.observe()
    direct_status = _direct_reconciliation_status(
        transition_id,
        fresh,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=task_state.get("staging_file_identity"),
        target_identity=task_state.get("target_file_identity"),
    )
    status, verification = _kernel_reconciliation_verification(
        attempt.revision_after,
        intent,
        transition_id,
        direct_status,
        fresh,
        task_id=task_id,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=task_state.get("staging_file_identity"),
        target_identity=task_state.get("target_file_identity"),
    )
    state = state.record_reconciliation(
        operation_id=intent.operation_id,
        attempt_revision=attempt.revision_after,
        status=status,
        verification=verification,
        expected_revision=state.revision,
    )
    task_state["working_state"] = state.as_dict()

    if status is ReconciliationStatus.CONFIRMED_NOT_APPLIED:
        task_state["prepared_intent"] = None
        checkpoint()
        return state, None, fresh

    if status is ReconciliationStatus.CONFIRMED_APPLIED:
        recovery_result = _commit_recovered_applied_transition(
            task_state,
            state,
            intent,
            transition_id,
            fresh,
            marker_action_count=int(marker["action_count_before"]),
            content_size=content_size,
            expected_sha=expected_sha,
            checkpoint=checkpoint,
        )
        return state, recovery_result, None

    task_state["status"] = "abstained"
    task_state["escalation_reason"] = "resume_reconciliation_unknown"
    checkpoint()
    return state, {
        "status": task_state["status"],
        "escalation_reason": task_state["escalation_reason"],
    }, None


def _reconcile_exceptional_delivery(
    task_state: dict[str, Any],
    state: WorkingState,
    intent: AttemptIntent,
    observer: FileArtifactObservationStream,
    *,
    transition_id: str,
    task_id: str,
    content_size: int,
    expected_sha: str,
    checkpoint: Callable[[], None],
) -> WorkingState:
    """Reconcile a delivery exception before deciding whether another act is safe."""

    marker = task_state.get("prepared_intent")
    if not isinstance(marker, dict):
        raise ValueError("prepared_intent disappeared during exceptional delivery")

    state = state.record_attempt(
        intent,
        MutatingOutcome.OUTCOME_UNKNOWN,
        _unknown_failure(intent),
        expected_revision=state.revision,
        guard=_WORKSPACE_GUARD,
    )
    attempt = state.attempts[-1]
    fresh = observer.observe()
    direct_status = _direct_reconciliation_status(
        transition_id,
        fresh,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=task_state.get("staging_file_identity"),
        target_identity=task_state.get("target_file_identity"),
    )
    status, verification = _kernel_reconciliation_verification(
        attempt.revision_after,
        intent,
        transition_id,
        direct_status,
        fresh,
        task_id=task_id,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=task_state.get("staging_file_identity"),
        target_identity=task_state.get("target_file_identity"),
    )
    state = state.record_reconciliation(
        operation_id=intent.operation_id,
        attempt_revision=attempt.revision_after,
        status=status,
        verification=verification,
        expected_revision=state.revision,
    )
    task_state["working_state"] = state.as_dict()

    if status is ReconciliationStatus.CONFIRMED_APPLIED:
        _commit_recovered_applied_transition(
            task_state,
            state,
            intent,
            transition_id,
            fresh,
            marker_action_count=int(marker["action_count_before"]),
            content_size=content_size,
            expected_sha=expected_sha,
            checkpoint=checkpoint,
        )
        return state

    if status is ReconciliationStatus.CONFIRMED_NOT_APPLIED:
        task_state["prepared_intent"] = None
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "delivery_error_confirmed_not_applied"
    else:
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "delivery_error_reconciliation_unknown"
    checkpoint()
    return state


def run_verified_workspace_artifact(
    request: dict[str, Any],
    *,
    workspace_root: Path,
    state_root: Path,
    candidate_admission: str | None,
) -> dict[str, Any]:
    """Run or resume the bounded verified workspace-artifact procedure."""

    started = time.monotonic()
    workspace_root = workspace_root.resolve()
    state_root = state_root.resolve()
    if not workspace_root.is_dir():
        raise ValueError("configured workspace root is not an existing directory")
    if candidate_admission != QUALIFICATION_ADMISSION:
        raise PermissionError("candidate procedure is not admitted by this profile")

    keys = set(request)
    required_keys = {"procedure", "artifact_name", "content"}
    allowed_keys = required_keys | {"resume_task_id"}
    if not required_keys.issubset(keys) or not keys.issubset(allowed_keys):
        raise ValueError(
            "procedure request must contain procedure, artifact_name, content and optional resume_task_id"
        )
    if request.get("procedure") != PROCEDURE_ID:
        raise ValueError("unknown or unregistered procedure")

    artifact_name = request.get("artifact_name")
    content = request.get("content")
    if not isinstance(artifact_name, str) or not _ARTIFACT_RE.fullmatch(artifact_name):
        raise ValueError("artifact_name must be a simple .txt file name")
    if not isinstance(content, str) or not content or len(content) > MAX_CONTENT_CHARS:
        raise ValueError("content must contain 1..4096 Unicode characters")
    if "\x00" in content:
        raise ValueError("content must not contain NUL")

    content_bytes = content.encode("utf-8")
    if len(content_bytes) > MAX_CONTENT_BYTES:
        raise ValueError("UTF-8 content exceeds the procedure byte budget")
    expected_sha = _sha256(content_bytes)

    reserved_root = _safe_child(
        workspace_root,
        workspace_root / Path(*RESERVED_WORKSPACE_DIR.split("/")),
    )
    target = _safe_child(reserved_root, reserved_root / artifact_name)
    relative_target = target.relative_to(workspace_root).as_posix()

    resume_task_id = request.get("resume_task_id")
    if resume_task_id is not None and (
        not isinstance(resume_task_id, str) or not _TASK_ID_RE.fullmatch(resume_task_id)
    ):
        raise ValueError("resume_task_id must be a 32-character lowercase hex task id")

    task_id = resume_task_id if resume_task_id is not None else secrets.token_hex(16)
    task_lock = _acquire_task_lock(state_root, task_id)
    try:
        return _run_verified_workspace_artifact_locked(
            started=started,
            workspace_root=workspace_root,
            state_root=state_root,
            artifact_name=artifact_name,
            content_bytes=content_bytes,
            expected_sha=expected_sha,
            reserved_root=reserved_root,
            target=target,
            relative_target=relative_target,
            resume_task_id=resume_task_id,
            task_id=task_id,
        )
    finally:
        task_lock.close()


def _run_verified_workspace_artifact_locked(
    *,
    started: float,
    workspace_root: Path,
    state_root: Path,
    artifact_name: str,
    content_bytes: bytes,
    expected_sha: str,
    reserved_root: Path,
    target: Path,
    relative_target: str,
    resume_task_id: str | None,
    task_id: str,
) -> dict[str, Any]:
    staging = _safe_child(reserved_root, reserved_root / f".{artifact_name}.{task_id}.staging")
    schema_version = CHECKPOINT_SCHEMA_VERSION
    working_state: WorkingState | None = None
    if resume_task_id is None:
        task_state: dict[str, Any] = {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "task_id": task_id,
            "procedure_id": PROCEDURE_ID,
            "procedure_version": PROCEDURE_VERSION,
            "procedure_status": PROCEDURE_STATUS,
            "artifact_name": artifact_name,
            "artifact_relative_path": relative_target,
            "content_sha256": expected_sha,
            "content_size": len(content_bytes),
            "current_node": "preflight",
            "status": "running",
            "action_count": 0,
            "action_budget": MAX_ACTIONS,
            "runtime_budget_seconds": MAX_RUNTIME_SECONDS,
            "transition_receipts": [],
            "escalation_reason": None,
            "staging_file_identity": None,
            "target_file_identity": None,
            "working_state": None,
            "prepared_intent": None,
            "created_at": _utc_now(),
        }
    else:
        task_state = _load_checkpoint(state_root, task_id)
        schema_version = _validate_resume_state(
            task_state,
            task_id=task_id,
            artifact_name=artifact_name,
            expected_sha=expected_sha,
            content_size=len(content_bytes),
            relative_target=relative_target,
        )
        task_state.setdefault("staging_file_identity", None)
        task_state.setdefault("target_file_identity", None)
        task_state["resumed_at"] = _utc_now()
        if schema_version == CHECKPOINT_SCHEMA_VERSION:
            working_state = _restore_working_state(task_state, task_id=task_id)

    if working_state is None:
        observer = FileArtifactObservationStream(
            root=workspace_root,
            subject=f"{PROCEDURE_ID}:{task_id}",
            paths={"staging": staging, "target": target},
            max_bytes=MAX_CONTENT_BYTES,
        )
    else:
        observer = FileArtifactObservationStream(
            root=workspace_root,
            subject=f"{PROCEDURE_ID}:{task_id}",
            paths={"staging": staging, "target": target},
            max_bytes=MAX_CONTENT_BYTES,
            stream_id=working_state.observation_ref.stream_id,
            initial_sequence=working_state.observation_ref.sequence,
        )

    def checkpoint() -> None:
        nonlocal working_state
        if int(task_state["action_count"]) > MAX_ACTIONS:
            raise RuntimeError("action budget exceeded")
        if time.monotonic() - started > MAX_RUNTIME_SECONDS:
            raise RuntimeError("runtime budget exceeded")
        if working_state is not None:
            task_state["schema_version"] = CHECKPOINT_SCHEMA_VERSION
            durable = task_state.get("working_state")
            durable_revision = (
                durable.get("revision", -1)
                if isinstance(durable, dict) and type(durable.get("revision")) is int
                else -1
            )
            if working_state.revision >= durable_revision:
                task_state["working_state"] = working_state.as_dict()
            task_state.setdefault("prepared_intent", None)
        _write_checkpoint(state_root, task_state)

    if (
        schema_version == 1
        and task_state["status"] == "completed"
        and not _legacy_identity_generation_proven(task_state.get("target_file_identity"))
    ):
        raise ValueError("legacy completed identity generation is unavailable")

    if task_state["status"] == "completed":
        completed_result, completed_snapshot = _verify_current_state(
            observer,
            effect_id="completed_checkpoint_current_state",
            predicates=(
                *_file_predicates(
                    "target",
                    size=len(content_bytes),
                    sha256=expected_sha,
                    identity=task_state.get("target_file_identity"),
                ),
                *_missing_predicates("staging"),
            ),
        )
        if completed_result.status is not VerificationStatus.PASS:
            raise ValueError("completed checkpoint no longer matches current target identity")
        final = _observed_evidence(completed_snapshot, "target")
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=final,
            rollback=task_state.get("rollback", {"staging_removed": True, "target_removed": False}),
            resumed=True,
        )

    if task_state["status"] != "running":
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=_evidence(target),
            rollback=task_state.get(
                "rollback",
                {"staging_removed": not staging.exists(), "target_removed": False},
            ),
            resumed=True,
        )

    node = str(task_state["current_node"])
    if node not in _RESUMABLE_NODES:
        raise ValueError("resume checkpoint node is not safely resumable")

    if schema_version == 1 and node in {"staged_verified", "final_verified"}:
        identities = [task_state.get("staging_file_identity")]
        if node == "final_verified":
            identities.append(task_state.get("target_file_identity"))
        if not all(_legacy_identity_generation_proven(item) for item in identities):
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "legacy_identity_generation_unproven"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_evidence(target),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=True,
            )

    reconciled_retry_snapshot: ObservationSnapshot | None = None
    if working_state is not None and task_state.get("prepared_intent") is not None:
        working_state, recovery_result, reconciled_retry_snapshot = _recover_prepared_intent(
            task_state,
            working_state,
            observer,
            task_id=task_id,
            relative_target=relative_target,
            expected_sha=expected_sha,
            content_size=len(content_bytes),
            checkpoint=checkpoint,
        )
        if recovery_result is not None:
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=recovery_result.get("final_verification", _evidence(target)),
                rollback=task_state.get(
                    "rollback",
                    {"staging_removed": not staging.exists(), "target_removed": False},
                ),
                resumed=True,
            )
        node = str(task_state["current_node"])

    if working_state is not None and working_state.unresolved_attempts():
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "resume_reconciliation_required"
        checkpoint()
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=_evidence(target),
            rollback={"staging_removed": not staging.exists(), "target_removed": False},
            resumed=resume_task_id is not None,
        )

    if working_state is not None and _same_node_applied_operation(
        working_state,
        task_id=task_id,
        node=node,
    ):
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "resume_verified_effect_without_transition_receipt"
        checkpoint()
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=_evidence(target),
            rollback={"staging_removed": not staging.exists(), "target_removed": False},
            resumed=resume_task_id is not None,
        )

    migrated_snapshot: ObservationSnapshot | None = reconciled_retry_snapshot

    if node == "preflight":
        if reconciled_retry_snapshot is None:
            preflight = observer.observe()
            if working_state is None:
                working_state = _new_working_state(task_id, preflight)
                task_state["schema_version"] = CHECKPOINT_SCHEMA_VERSION
                task_state["working_state"] = working_state.as_dict()
                task_state["prepared_intent"] = None
            else:
                working_state = _advance_working_observation(working_state, preflight)
        else:
            preflight = reconciled_retry_snapshot
        migrated_snapshot = preflight
        if preflight.ambiguous:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "preflight_observation_unknown"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_observed_evidence(preflight, "target"),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=resume_task_id is not None,
            )
        if preflight.state["target"].get("exists") is True:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "target_already_exists"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_observed_evidence(preflight, "target"),
                rollback={"staging_removed": True, "target_removed": False},
                resumed=resume_task_id is not None,
            )
        if preflight.state["staging"].get("exists") is True:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "unexpected_staging_state"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_observed_evidence(preflight, "target"),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=resume_task_id is not None,
            )
        checkpoint()
    elif node == "staged_verified":
        legacy_identity = task_state.get("staging_file_identity")
        if reconciled_retry_snapshot is None:
            resume_staged, resume_staged_snapshot = _verify_current_state(
                observer,
                effect_id="resume_staged_current_state",
                predicates=(
                    *_file_predicates(
                        "staging",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=(legacy_identity if working_state is not None else None),
                    ),
                    *_missing_predicates("target"),
                ),
            )
            if (
                resume_staged.status is not VerificationStatus.PASS
                or (working_state is None and not _same_file_identity(staging, legacy_identity))
            ):
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = (
                    "resume_unexpected_target_state"
                    if resume_staged_snapshot.state["target"].get("exists") is True
                    else "resume_staging_identity_mismatch"
                )
                checkpoint()
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback={"staging_removed": False, "target_removed": False},
                    resumed=True,
                )
        else:
            resume_staged_snapshot = reconciled_retry_snapshot
        upgraded_staging_identity = _observed_identity(resume_staged_snapshot, "staging")
        if upgraded_staging_identity is None:
            raise ValueError("resume staging identity is unavailable")
        task_state["staging_file_identity"] = upgraded_staging_identity
        migrated_snapshot = resume_staged_snapshot
        if working_state is None:
            working_state = _new_working_state(task_id, resume_staged_snapshot)
            task_state["schema_version"] = CHECKPOINT_SCHEMA_VERSION
            task_state["prepared_intent"] = None
        else:
            working_state = _advance_working_observation(
                working_state,
                resume_staged_snapshot,
            )
        checkpoint()
    elif node == "final_verified":
        legacy_staging_identity = task_state.get("staging_file_identity")
        legacy_target_identity = task_state.get("target_file_identity")
        if reconciled_retry_snapshot is None:
            resume_final, resume_final_snapshot = _verify_current_state(
                observer,
                effect_id="resume_final_current_state",
                predicates=(
                    *_file_predicates(
                        "staging",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=(legacy_staging_identity if working_state is not None else None),
                    ),
                    *_file_predicates(
                        "target",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=(legacy_target_identity if working_state is not None else None),
                    ),
                ),
            )
            if (
                resume_final.status is not VerificationStatus.PASS
                or (
                    working_state is None
                    and (
                        not _same_file_identity(staging, legacy_staging_identity)
                        or not _same_file_identity(target, legacy_target_identity)
                    )
                )
            ):
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "resume_final_identity_mismatch"
                checkpoint()
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback={"staging_removed": False, "target_removed": False},
                    resumed=True,
                )
        else:
            resume_final_snapshot = reconciled_retry_snapshot
        upgraded_staging_identity = _observed_identity(resume_final_snapshot, "staging")
        upgraded_target_identity = _observed_identity(resume_final_snapshot, "target")
        if upgraded_staging_identity is None or upgraded_target_identity is None:
            raise ValueError("resume final identity is unavailable")
        task_state["staging_file_identity"] = upgraded_staging_identity
        task_state["target_file_identity"] = upgraded_target_identity
        migrated_snapshot = resume_final_snapshot
        if working_state is None:
            working_state = _new_working_state(task_id, resume_final_snapshot)
            task_state["schema_version"] = CHECKPOINT_SCHEMA_VERSION
            task_state["prepared_intent"] = None
        else:
            working_state = _advance_working_observation(
                working_state,
                resume_final_snapshot,
            )
        checkpoint()

    if working_state is None or migrated_snapshot is None:
        raise RuntimeError("WorkingState initialization failed")

    reserved_root.mkdir(parents=True, exist_ok=True)
    staging_owned = False
    target_owned = False
    rollback = {"staging_removed": not staging.exists(), "target_removed": False}

    try:
        if node == "preflight":
            if reconciled_retry_snapshot is None:
                stage_before = observer.observe()
                working_state = _advance_working_observation(working_state, stage_before)
            else:
                stage_before = reconciled_retry_snapshot
            intent = _prepare_transition(
                task_state,
                working_state,
                task_id=task_id,
                transition_id="stage_create",
                relative_target=relative_target,
                expected_sha=expected_sha,
                content_size=len(content_bytes),
                checkpoint=checkpoint,
            )
            try:
                _exclusive_create_file(staging, content_bytes)
            except FileExistsError:
                stage_after = observer.observe()
                working_state = _record_file_exists_no_effect(
                    task_state,
                    working_state,
                    intent,
                    stage_after,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )
            except Exception:
                working_state = _reconcile_exceptional_delivery(
                    task_state,
                    working_state,
                    intent,
                    observer,
                    transition_id="stage_create",
                    task_id=task_id,
                    content_size=len(content_bytes),
                    expected_sha=expected_sha,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )

            stage_after = observer.observe()
            direct_status = _direct_reconciliation_status(
                "stage_create",
                stage_after,
                content_size=len(content_bytes),
                expected_sha=expected_sha,
                staging_identity=None,
            )
            staging_identity = _observed_identity(stage_after, "staging")
            stage_result = _verify_transition(
                effect_id="stage_create",
                before=stage_before,
                after=stage_after,
                predicates=(
                    *_file_predicates(
                        "staging",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=staging_identity,
                    ),
                    *_missing_predicates("target"),
                ),
            )
            authoritative_status = _authoritative_normal_status(
                direct_status,
                kernel_pass=(
                    stage_result.status is VerificationStatus.PASS
                    and staging_identity is not None
                ),
            )
            working_state = _record_normal_outcome(
                working_state,
                intent,
                authoritative_status,
                stage_after,
                task_id=task_id,
            )
            task_state["action_count"] = int(task_state["action_count"]) + 1
            task_state["working_state"] = working_state.as_dict()
            task_state["prepared_intent"] = None
            if authoritative_status is not ReconciliationStatus.CONFIRMED_APPLIED:
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "staging_postcondition_failed"
                checkpoint()
                raise RuntimeError("staging postcondition failed")
            task_state["staging_file_identity"] = staging_identity
            staging_owned = True
            _record_transition(
                task_state,
                transition_id="stage_create",
                from_node="preflight",
                to_node="staged_verified",
                action="exclusive_create_staging",
                verification=_observed_evidence(stage_after, "staging"),
                kernel_verification=_kernel_receipt(stage_result),
            )
            checkpoint()
            node = "staged_verified"
            reconciled_retry_snapshot = None

        if node == "staged_verified":
            if reconciled_retry_snapshot is None:
                final_before_check, final_before = _verify_current_state(
                    observer,
                    effect_id="final_create_precondition",
                    predicates=(
                        *_file_predicates(
                            "staging",
                            size=len(content_bytes),
                            sha256=expected_sha,
                            identity=task_state.get("staging_file_identity"),
                        ),
                        *_missing_predicates("target"),
                    ),
                )
                working_state = _advance_working_observation(working_state, final_before)
                if final_before_check.status is not VerificationStatus.PASS:
                    task_state["status"] = "abstained"
                    task_state["escalation_reason"] = "final_create_precondition_failed"
                    checkpoint()
                    raise RuntimeError("final create precondition failed")
            else:
                final_before = reconciled_retry_snapshot
            intent = _prepare_transition(
                task_state,
                working_state,
                task_id=task_id,
                transition_id="final_create",
                relative_target=relative_target,
                expected_sha=expected_sha,
                content_size=len(content_bytes),
                checkpoint=checkpoint,
            )
            try:
                with pin_file_for_verified_link(staging):
                    pinned_staging = _evidence(staging)
                    if (
                        not _same_file_identity(
                            staging,
                            task_state.get("staging_file_identity"),
                        )
                        or pinned_staging["size"] != len(content_bytes)
                        or pinned_staging["sha256"] != expected_sha
                    ):
                        raise RuntimeError(
                            "verified staging changed before final hard-link delivery"
                        )
                    _exclusive_link_file(staging, target)
            except FileExistsError:
                final_after = observer.observe()
                working_state = _record_file_exists_no_effect(
                    task_state,
                    working_state,
                    intent,
                    final_after,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )
            except Exception:
                working_state = _reconcile_exceptional_delivery(
                    task_state,
                    working_state,
                    intent,
                    observer,
                    transition_id="final_create",
                    task_id=task_id,
                    content_size=len(content_bytes),
                    expected_sha=expected_sha,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )

            final_after = observer.observe()
            staging_identity = _normalized_identity(task_state.get("staging_file_identity"))
            direct_status = _direct_reconciliation_status(
                "final_create",
                final_after,
                content_size=len(content_bytes),
                expected_sha=expected_sha,
                staging_identity=staging_identity,
                target_identity=staging_identity,
            )
            final_result = _verify_transition(
                effect_id="final_create",
                before=final_before,
                after=final_after,
                predicates=(
                    *_file_predicates(
                        "staging",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=staging_identity,
                    ),
                    *_file_predicates(
                        "target",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=staging_identity,
                    ),
                ),
            )
            target_identity = _observed_identity(final_after, "target")
            authoritative_status = _authoritative_normal_status(
                direct_status,
                kernel_pass=(
                    final_result.status is VerificationStatus.PASS
                    and staging_identity is not None
                    and target_identity == staging_identity
                ),
            )
            working_state = _record_normal_outcome(
                working_state,
                intent,
                authoritative_status,
                final_after,
                task_id=task_id,
            )
            task_state["action_count"] = int(task_state["action_count"]) + 1
            task_state["working_state"] = working_state.as_dict()
            task_state["prepared_intent"] = None
            if authoritative_status is not ReconciliationStatus.CONFIRMED_APPLIED:
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "final_create_postcondition_failed"
                checkpoint()
                raise RuntimeError("final create postcondition failed")
            task_state["target_file_identity"] = staging_identity
            target_owned = True
            _record_transition(
                task_state,
                transition_id="final_create",
                from_node="staged_verified",
                to_node="final_verified",
                action="hardlink_verified_staging_to_final",
                verification={
                    "target": _observed_evidence(final_after, "target"),
                    "staging": _observed_evidence(final_after, "staging"),
                },
                kernel_verification=_kernel_receipt(final_result),
            )
            checkpoint()
            node = "final_verified"
            reconciled_retry_snapshot = None

        if node == "final_verified":
            if reconciled_retry_snapshot is None:
                cleanup_before_check, cleanup_before = _verify_current_state(
                    observer,
                    effect_id="staging_cleanup_precondition",
                    predicates=(
                        *_file_predicates(
                            "staging",
                            size=len(content_bytes),
                            sha256=expected_sha,
                            identity=task_state.get("staging_file_identity"),
                        ),
                        *_file_predicates(
                            "target",
                            size=len(content_bytes),
                            sha256=expected_sha,
                            identity=task_state.get("target_file_identity"),
                        ),
                    ),
                )
                working_state = _advance_working_observation(working_state, cleanup_before)
                if cleanup_before_check.status is not VerificationStatus.PASS:
                    task_state["status"] = "abstained"
                    task_state["escalation_reason"] = "cleanup_precondition_failed"
                    checkpoint()
                    raise RuntimeError("cleanup precondition failed")
            else:
                cleanup_before = reconciled_retry_snapshot
            intent = _prepare_transition(
                task_state,
                working_state,
                task_id=task_id,
                transition_id="staging_cleanup",
                relative_target=relative_target,
                expected_sha=expected_sha,
                content_size=len(content_bytes),
                checkpoint=checkpoint,
            )
            try:
                staging.unlink()
            except Exception:
                working_state = _reconcile_exceptional_delivery(
                    task_state,
                    working_state,
                    intent,
                    observer,
                    transition_id="staging_cleanup",
                    task_id=task_id,
                    content_size=len(content_bytes),
                    expected_sha=expected_sha,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )

            completion_after = observer.observe()
            staging_identity = _normalized_identity(task_state.get("staging_file_identity"))
            target_identity = _normalized_identity(task_state.get("target_file_identity"))
            direct_status = _direct_reconciliation_status(
                "staging_cleanup",
                completion_after,
                content_size=len(content_bytes),
                expected_sha=expected_sha,
                staging_identity=staging_identity,
                target_identity=target_identity,
            )
            evidence_batch_id = f"{task_id}:completion:{int(task_state['action_count']) + 1}"
            goal_result = _verify_transition(
                effect_id="completion_target",
                before=cleanup_before,
                after=completion_after,
                predicates=_file_predicates(
                    "target",
                    size=len(content_bytes),
                    sha256=expected_sha,
                    identity=target_identity,
                ),
                evidence_batch_id=evidence_batch_id,
            )
            safety_result = _verify_transition(
                effect_id="completion_staging_absent",
                before=cleanup_before,
                after=completion_after,
                predicates=_missing_predicates("staging"),
                evidence_batch_id=evidence_batch_id,
            )
            finish_gate = evaluate_finish_gate(
                evidence_batch_id=evidence_batch_id,
                candidate_done=True,
                goal_results=(goal_result,),
                safety_results=(safety_result,),
            )
            authoritative_status = _authoritative_normal_status(
                direct_status,
                kernel_pass=finish_gate.status is FinishStatus.DONE,
            )
            working_state = _record_normal_outcome(
                working_state,
                intent,
                authoritative_status,
                completion_after,
                task_id=task_id,
            )
            task_state["action_count"] = int(task_state["action_count"]) + 1
            task_state["working_state"] = working_state.as_dict()
            task_state["prepared_intent"] = None
            staging_owned = False
            final_verification = _observed_evidence(completion_after, "target")
            if authoritative_status is not ReconciliationStatus.CONFIRMED_APPLIED:
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "completion_postcondition_failed"
                checkpoint()
                raise RuntimeError("completion postcondition failed")
            _record_transition(
                task_state,
                transition_id="staging_cleanup",
                from_node="final_verified",
                to_node="completed",
                action="remove_verified_staging",
                verification={"target": final_verification, "staging_exists": False},
                kernel_verification={
                    "goal": _kernel_receipt(goal_result),
                    "safety": _kernel_receipt(safety_result),
                    "finish_gate": finish_gate.as_dict(),
                },
            )
            task_state["status"] = "completed"
            task_state["completed_at"] = _utc_now()
            task_state["rollback"] = dict(rollback)
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=final_verification,
                rollback=rollback,
                resumed=resume_task_id is not None,
            )
    except Exception as exc:
        if task_state["status"] != "abstained":
            task_state["status"] = "failed"
            task_state["escalation_reason"] = f"runtime_error:{type(exc).__name__}"
    finally:
        if task_state["status"] != "completed":
            safe_to_compensate = (
                task_state["status"] != "running"
                and task_state.get("prepared_intent") is None
                and working_state is not None
                and not working_state.unresolved_attempts()
            )
            changed = False
            if safe_to_compensate and staging_owned:
                rollback["staging_removed"] = _rollback_owned_file(
                    staging,
                    expected_sha,
                    task_state.get("staging_file_identity"),
                )
                changed = changed or rollback["staging_removed"]
            if safe_to_compensate and target_owned:
                rollback["target_removed"] = _rollback_owned_file(
                    target,
                    expected_sha,
                    task_state.get("target_file_identity"),
                )
                changed = changed or rollback["target_removed"]
            if changed and working_state is not None:
                try:
                    rollback_snapshot = observer.observe()
                    working_state = _advance_working_observation(
                        working_state,
                        rollback_snapshot,
                    )
                    task_state["working_state"] = working_state.as_dict()
                except Exception:
                    pass
            task_state["rollback"] = dict(rollback)
            task_state["finished_at"] = _utc_now()
            try:
                checkpoint()
            except Exception:
                pass

    return _result(
        task_state,
        artifact_relative_path=relative_target,
        final_verification=_evidence(target),
        rollback=rollback,
        resumed=resume_task_id is not None,
    )