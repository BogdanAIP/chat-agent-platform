from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .authorization import AuthorizationRequest, CapabilityGrant
from .verification import ObservationSnapshot, VerificationStatus, evaluate_finish_gate
from .windows_observation import WINDOWS_DESKTOP_CAPABILITY, WindowsDesktopObservationStream
from .windows_transition import verify_windows_desktop_snapshots
from .working_state import (
    AttemptIntent,
    FailureCategory,
    FailureReason,
    LoopGuard,
    MutatingOutcome,
    WorkingState,
)


PROCEDURE_ID = "windows_case_update_v1"
PROCEDURE_VERSION = "1"
PROCEDURE_STATUS = "candidate"
QUALIFICATION_ADMISSION = "stage26-3b-windows-l3"
MAX_NOTE_CHARS = 512
MAX_ACTIONS = 5
MAX_RUNTIME_SECONDS = 90.0
POSTCONDITION_SETTLE_SECONDS = 2.0
POSTCONDITION_POLL_SECONDS = 0.08
_TRANSITIONS = (
    "select_case",
    "focus_note",
    "enter_note",
    "set_status",
    "save_case",
)
_WORKING_ACTOR = "procedure:windows_case_update_v1"
_WINDOWS_GUARD = LoopGuard()
_ALLOWED_STATUSES = {"Approved", "Needs Review"}
_CASE_ID_RE = re.compile(r"^CASE-([A-F0-9]{8})-([0-9]{4})$")
_RUN_ID_RE = re.compile(r"^[A-F0-9]{8}$")
_HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
_STATE_TOKEN_RE = re.compile(
    r"^STATE\|selected=(?P<selected>NONE|CASE-[A-F0-9]{8}-[0-9]{4})"
    r"\|draft_status=(?P<status>NONE|Approved|Needs Review)"
    r"\|note_sha256=(?P<note>[0-9a-f]{64})"
    r"\|saved=(?P<saved>[0-9]+)$"
)
_CASE_SUMMARY_RE = re.compile(
    r"^CASESTATE\|id=(?P<id>CASE-[A-F0-9]{8}-[0-9]{4})"
    r"\|status=(?P<status>Pending|Approved|Needs Review)"
    r"\|notes=(?P<notes>[0-9]+)$"
)
_TASK_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class ProcedureAbstained(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _windows_case_resource_scope_ref(
    *,
    run_id: str,
    expected_head: str,
    case_id: str,
    note_sha256: str,
    requested_status: str,
) -> str:
    return "windows-case:" + _canonical_digest(
        {
            "run_id": run_id,
            "expected_head": expected_head,
            "case_id": case_id,
            "note_sha256": note_sha256,
            "requested_status": requested_status,
        }
    )


def _windows_case_grant_ref(
    *,
    task_id: str,
    run_id: str,
    expected_head: str,
    case_id: str,
    note_sha256: str,
    requested_status: str,
) -> str:
    return "grant:windows-case:" + _canonical_digest(
        {
            "procedure": PROCEDURE_ID,
            "version": PROCEDURE_VERSION,
            "admission": QUALIFICATION_ADMISSION,
            "task_id": task_id,
            "resource_scope_ref": _windows_case_resource_scope_ref(
                run_id=run_id,
                expected_head=expected_head,
                case_id=case_id,
                note_sha256=note_sha256,
                requested_status=requested_status,
            ),
        }
    )


def _windows_environment_ref(expected_head: str) -> str:
    return f"windows-case-l3:head:{expected_head}"


def _windows_case_grant(
    state: WorkingState,
    *,
    task_id: str,
    run_id: str,
    expected_head: str,
    case_id: str,
    note_sha256: str,
    requested_status: str,
) -> CapabilityGrant:
    return CapabilityGrant(
        grant_ref=_windows_case_grant_ref(
            task_id=task_id,
            run_id=run_id,
            expected_head=expected_head,
            case_id=case_id,
            note_sha256=note_sha256,
            requested_status=requested_status,
        ),
        task_ref=task_id,
        principal_ref=_WORKING_ACTOR,
        capability=WINDOWS_DESKTOP_CAPABILITY,
        allowed_action_refs=_TRANSITIONS,
        resource_scope_ref=_windows_case_resource_scope_ref(
            run_id=run_id,
            expected_head=expected_head,
            case_id=case_id,
            note_sha256=note_sha256,
            requested_status=requested_status,
        ),
        execution_environment_ref=_windows_environment_ref(expected_head),
        evidence_scope_ref=state.evidence_scope_ref,
    )


def _windows_case_intent(
    state: WorkingState,
    *,
    task_id: str,
    transition_id: str,
    run_id: str,
    expected_head: str,
    case_id: str,
    note_sha256: str,
    requested_status: str,
) -> AttemptIntent:
    resource_scope_ref = _windows_case_resource_scope_ref(
        run_id=run_id,
        expected_head=expected_head,
        case_id=case_id,
        note_sha256=note_sha256,
        requested_status=requested_status,
    )
    action_fingerprint = _canonical_digest(
        {
            "procedure": PROCEDURE_ID,
            "version": PROCEDURE_VERSION,
            "task_id": task_id,
            "transition": transition_id,
            "resource_scope_ref": resource_scope_ref,
        }
    )
    return AttemptIntent(
        operation_id=f"{task_id}:{transition_id}",
        strategy_id=transition_id,
        action_fingerprint=action_fingerprint,
        observation_ref=state.observation_ref,
        actor_ref=_WORKING_ACTOR,
        execution_environment_ref=_windows_environment_ref(expected_head),
        evidence_scope_ref=state.evidence_scope_ref,
        evidence_refs=(
            f"observation:{state.observation_ref.stream_id}:{state.observation_ref.sequence}",
        ),
    )


def _windows_case_authorization_request(
    state: WorkingState,
    intent: AttemptIntent,
    *,
    transition_id: str,
    run_id: str,
    expected_head: str,
    case_id: str,
    note_sha256: str,
    requested_status: str,
) -> AuthorizationRequest:
    return AuthorizationRequest(
        task_ref=state.task_id,
        principal_ref=_WORKING_ACTOR,
        capability=WINDOWS_DESKTOP_CAPABILITY,
        action_ref=transition_id,
        resource_scope_ref=_windows_case_resource_scope_ref(
            run_id=run_id,
            expected_head=expected_head,
            case_id=case_id,
            note_sha256=note_sha256,
            requested_status=requested_status,
        ),
        attempt_authorization_fingerprint=intent.authorization_fingerprint,
        execution_environment_ref=_windows_environment_ref(expected_head),
        evidence_scope_ref=state.evidence_scope_ref,
    )


def _windows_case_guard_decision(
    state: WorkingState,
    intent: AttemptIntent,
    *,
    transition_id: str,
    task_id: str,
    run_id: str,
    expected_head: str,
    case_id: str,
    note_sha256: str,
    requested_status: str,
):
    return _WINDOWS_GUARD.evaluate_authorized(
        state,
        intent,
        authorization_request=_windows_case_authorization_request(
            state,
            intent,
            transition_id=transition_id,
            run_id=run_id,
            expected_head=expected_head,
            case_id=case_id,
            note_sha256=note_sha256,
            requested_status=requested_status,
        ),
        capability_grant=_windows_case_grant(
            state,
            task_id=task_id,
            run_id=run_id,
            expected_head=expected_head,
            case_id=case_id,
            note_sha256=note_sha256,
            requested_status=requested_status,
        ),
        expected_revision=state.revision,
    )


def _windows_unknown_failure(intent: AttemptIntent) -> FailureReason:
    return FailureReason(
        code="windows_transition_outcome_unknown",
        category=FailureCategory.RECONCILIATION_REQUIRED,
        message="Windows transition final state was not verified; no later physical action is safe.",
        retryable=False,
        reconciliation_required=True,
        operation_id=intent.operation_id,
        strategy_id=intent.strategy_id,
        outcome=MutatingOutcome.OUTCOME_UNKNOWN,
        evidence_refs=intent.evidence_refs,
    )


def _record_windows_case_attempt(
    state: WorkingState,
    intent: AttemptIntent,
    outcome: MutatingOutcome,
    failure: FailureReason | None,
    *,
    transition_id: str,
    task_id: str,
    run_id: str,
    expected_head: str,
    case_id: str,
    note_sha256: str,
    requested_status: str,
) -> WorkingState:
    return state.record_authorized_attempt(
        intent,
        outcome,
        failure,
        authorization_request=_windows_case_authorization_request(
            state,
            intent,
            transition_id=transition_id,
            run_id=run_id,
            expected_head=expected_head,
            case_id=case_id,
            note_sha256=note_sha256,
            requested_status=requested_status,
        ),
        capability_grant=_windows_case_grant(
            state,
            task_id=task_id,
            run_id=run_id,
            expected_head=expected_head,
            case_id=case_id,
            note_sha256=note_sha256,
            requested_status=requested_status,
        ),
        expected_revision=state.revision,
        guard=_WINDOWS_GUARD,
    )


def _new_windows_working_state(
    *,
    task_id: str,
    initial: ObservationSnapshot,
    run_id: str,
    expected_head: str,
    case_id: str,
    note_sha256: str,
    requested_status: str,
) -> WorkingState:
    grant_ref = _windows_case_grant_ref(
        task_id=task_id,
        run_id=run_id,
        expected_head=expected_head,
        case_id=case_id,
        note_sha256=note_sha256,
        requested_status=requested_status,
    )
    return WorkingState.create(
        task_id=task_id,
        task_budget=MAX_ACTIONS,
        procedure_budget=MAX_ACTIONS,
        strategy_budgets={transition: 1 for transition in _TRANSITIONS},
        observation_ref=initial.ref,
        actor_ref=_WORKING_ACTOR,
        execution_environment_ref=_windows_environment_ref(expected_head),
        evidence_scope_ref=initial.ref.stream_id,
        procedure_ref=PROCEDURE_ID,
        user_constraints=("active-session-bound", "external-finish-gate-required"),
        subgoal_refs=_TRANSITIONS,
        evidence_refs=(
            f"observation:{initial.ref.stream_id}:{initial.ref.sequence}",
        ),
        capability_grant_refs=(grant_ref,),
    )


def _kernel_receipt(result: dict[str, Any]) -> dict[str, Any]:
    verification = result["verification"]
    return {
        "status": result["status"],
        "reason": verification["reason"],
        "effect_id": verification["effect_id"],
        "observation": verification["observation"],
        "evidence_batch_id": verification.get("evidence_batch_id"),
        "predicate_results": verification.get("predicate_results", []),
    }


def _checkpoint_path(state_root: Path, task_id: str) -> Path:
    if not _TASK_ID_RE.fullmatch(task_id):
        raise ValueError("invalid task id")
    root = state_root.resolve()
    path = (root / f"{task_id}.json").resolve(strict=False)
    if path.parent != root:
        raise ValueError("checkpoint path escaped its configured root")
    return path


def _write_checkpoint(state_root: Path, task_state: dict[str, Any]) -> None:
    state_root.mkdir(parents=True, exist_ok=True)
    destination = _checkpoint_path(state_root, str(task_state["task_id"]))
    temporary = destination.with_name(f".{destination.name}.{secrets.token_hex(4)}.tmp")
    payload = json.dumps(task_state, ensure_ascii=False, indent=2, sort_keys=True)
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _active_session_path() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise RuntimeError("LOCALAPPDATA is unavailable")
    return (
        Path(local)
        / "ChatAgentPlatform"
        / "stage26"
        / "windows-case-l3"
        / "active-session.json"
    ).resolve()


def _parse_time(value: Any, *, name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _load_active_session() -> dict[str, Any]:
    path = _active_session_path()
    if not path.is_file() or path.is_symlink():
        raise ProcedureAbstained("windows_case_session_not_prepared")
    try:
        session = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ProcedureAbstained("windows_case_session_invalid") from exc
    required = {
        "schema_version",
        "qualification_kind",
        "run_id",
        "fixture_pid",
        "window_name",
        "expected_head",
        "created_at",
        "expires_at",
    }
    if not isinstance(session, dict) or set(session) != required:
        raise ProcedureAbstained("windows_case_session_shape_mismatch")
    if session["schema_version"] != 1 or session["qualification_kind"] != "windows-case-l3":
        raise ProcedureAbstained("windows_case_session_contract_mismatch")
    run_id = session["run_id"]
    if not isinstance(run_id, str) or not _RUN_ID_RE.fullmatch(run_id):
        raise ProcedureAbstained("windows_case_session_run_id_invalid")
    pid = session["fixture_pid"]
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise ProcedureAbstained("windows_case_session_pid_invalid")
    window_name = session["window_name"]
    if window_name != f"Case Desk {run_id}":
        raise ProcedureAbstained("windows_case_session_window_mismatch")
    expected_head = session["expected_head"]
    if not isinstance(expected_head, str) or not _HEAD_RE.fullmatch(expected_head):
        raise ProcedureAbstained("windows_case_session_head_invalid")
    try:
        _parse_time(session["created_at"], name="created_at")
        expires_at = _parse_time(session["expires_at"], name="expires_at")
    except ValueError as exc:
        raise ProcedureAbstained("windows_case_session_time_invalid") from exc
    if datetime.now(timezone.utc) >= expires_at:
        raise ProcedureAbstained("windows_case_session_expired")
    return session


def _validate_request(request: dict[str, Any], *, run_id: str) -> tuple[str, str, str]:
    if not isinstance(request, dict):
        raise ValueError("procedure request must be an object")
    required = {"procedure", "case_id", "note", "status"}
    if set(request) != required:
        raise ValueError("windows case request requires procedure, case_id, note and status only")
    if request.get("procedure") != PROCEDURE_ID:
        raise ValueError("unknown or unregistered procedure")
    case_id = request.get("case_id")
    match = _CASE_ID_RE.fullmatch(case_id) if isinstance(case_id, str) else None
    if match is None:
        raise ValueError("case_id must use CASE-XXXXXXXX-0000 format")
    if match.group(1) != run_id:
        raise ProcedureAbstained("case_id_does_not_belong_to_active_session")
    note = request.get("note")
    if not isinstance(note, str) or not note or len(note) > MAX_NOTE_CHARS:
        raise ValueError("note must contain 1..512 Unicode characters")
    if any(character in note for character in ("\x00", "\r", "\n")):
        raise ValueError("note must be a single line without NUL")
    status = request.get("status")
    if status not in _ALLOWED_STATUSES:
        raise ValueError("status must be Approved or Needs Review")
    return case_id, note, status


def _state_token(*, selected: str, status: str, note_sha256: str, saved: int) -> str:
    return (
        f"STATE|selected={selected}|draft_status={status}"
        f"|note_sha256={note_sha256}|saved={saved}"
    )


def _extract_state_token(visible_text: str) -> str:
    matches = [line for line in visible_text.splitlines() if line.startswith("STATE|")]
    if len(matches) != 1 or _STATE_TOKEN_RE.fullmatch(matches[0]) is None:
        raise ProcedureAbstained("case_desk_state_token_ambiguous")
    return matches[0]


def _extract_case_summary(visible_text: str, case_id: str) -> tuple[str, int, str]:
    matches: list[tuple[str, int, str]] = []
    for line in visible_text.splitlines():
        parsed = _CASE_SUMMARY_RE.fullmatch(line)
        if parsed and parsed.group("id") == case_id:
            matches.append((parsed.group("status"), int(parsed.group("notes")), line))
    if len(matches) != 1:
        raise ProcedureAbstained("target_case_summary_not_unique")
    return matches[0]


def _replace_visible_lines(visible_text: str, replacements: dict[str, str]) -> str:
    lines = visible_text.splitlines()
    counts = {old: 0 for old in replacements}
    output: list[str] = []
    for line in lines:
        if line in replacements:
            counts[line] += 1
            output.append(replacements[line])
        else:
            output.append(line)
    if any(count != 1 for count in counts.values()):
        raise ProcedureAbstained("expected_visible_evidence_not_unique")
    return "\n".join(output)


def _control_fingerprint(
    raw: dict[str, Any],
    *,
    role: str,
    name: str,
    focused: bool | None = None,
) -> str:
    matches = [
        item
        for item in raw.get("controls", [])
        if item.get("role") == role and item.get("name") == name
    ]
    if len(matches) != 1:
        raise ProcedureAbstained("expected_control_not_unique")
    item = matches[0]
    if focused is None:
        fingerprint = item.get("observation_fingerprint")
        if not isinstance(fingerprint, str):
            raise ProcedureAbstained("expected_control_fingerprint_missing")
        return fingerprint

    payload = {
        "role": str(item.get("role") or ""),
        "name": " ".join(str(item.get("name") or "").split()),
        "automation_id": str(item.get("automation_id") or ""),
        "bounds": item.get("bounds"),
        "enabled": item.get("enabled"),
        "visible": item.get("visible"),
        "focused": focused,
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _verification(
    *,
    before: ObservationSnapshot,
    after: ObservationSnapshot,
    expected: dict[str, Any],
    evidence_batch_id: str | None = None,
) -> dict[str, Any]:
    result, normalized_expected = verify_windows_desktop_snapshots(
        before=before,
        after=after,
        expected=expected,
        evidence_batch_id=evidence_batch_id,
    )
    return {
        "schema_version": 2,
        "operation": "verify_windows_desktop_transition",
        "status": result.status.value,
        "expected": normalized_expected,
        "before": before.ref.as_dict(),
        "after": after.ref.as_dict(),
        "verification": result.as_dict(),
    }


def _settle_postcondition(
    observe_fn: Callable[[], Any],
    verify_fn: Callable[[Any], dict[str, Any]],
    *,
    timeout_seconds: float = POSTCONDITION_SETTLE_SECONDS,
    poll_seconds: float = POSTCONDITION_POLL_SECONDS,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Bound verification to one action while allowing asynchronous UI state to settle.

    The action is never repeated here. Each attempt is a new authoritative
    observation verified against the same already-bound ExpectedEffect. A
    previous FAIL/UNKNOWN is not rewritten; PASS is accepted only from a later
    fresh observation that independently satisfies the postcondition.
    """

    if timeout_seconds < 0:
        raise ValueError("timeout_seconds must be non-negative")
    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be positive")

    deadline = time.monotonic() + timeout_seconds
    statuses: list[str] = []
    after: Any | None = None
    result: dict[str, Any] | None = None

    while True:
        after = observe_fn()
        result = verify_fn(after)
        status = str(result.get("status") or "")
        if status not in {
            VerificationStatus.PASS.value,
            VerificationStatus.FAIL.value,
            VerificationStatus.UNKNOWN.value,
        }:
            raise ProcedureAbstained("postcondition_verifier_returned_invalid_status")
        statuses.append(status)
        if status == VerificationStatus.PASS.value:
            break

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(poll_seconds, remaining))

    assert after is not None and result is not None
    return (
        after,
        result,
        {
            "attempt_count": len(statuses),
            "statuses": statuses,
            "settle_timeout_seconds": timeout_seconds,
        },
    )


def _receipt_mapping(receipt: Any) -> dict[str, Any]:
    return {
        "operation": str(getattr(receipt, "operation", "")),
        "native": bool(getattr(receipt, "native", False)),
        "outcome_verified": bool(getattr(receipt, "outcome_verified", False)),
        "target_fingerprint": getattr(receipt, "target_fingerprint", None),
    }


def _record_transition(
    task_state: dict[str, Any],
    *,
    transition_id: str,
    from_node: str,
    to_node: str,
    delivery: dict[str, Any],
    verification: dict[str, Any],
    postcondition_observation: dict[str, Any] | None = None,
) -> None:
    task_state["transition_receipts"].append(
        {
            "transition_id": transition_id,
            "from_node": from_node,
            "to_node": to_node,
            "delivery": delivery,
            "kernel_verification": _kernel_receipt(verification),
            "postcondition_observation": postcondition_observation,
            "verified_at": _utc_now(),
        }
    )
    if verification["status"] == VerificationStatus.PASS.value:
        task_state["current_node"] = to_node


def _result(task_state: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "procedure_id": PROCEDURE_ID,
        "procedure_version": PROCEDURE_VERSION,
        "procedure_status": PROCEDURE_STATUS,
        "task_id": task_state["task_id"],
        "status": task_state["status"],
        "current_node": task_state["current_node"],
        "action_count": task_state["action_count"],
        "transition_receipts": list(task_state["transition_receipts"]),
        "finish_gate": task_state.get("finish_gate"),
        "escalation_reason": task_state.get("escalation_reason"),
        **extra,
    }


def run_windows_case_update(
    request: dict[str, Any],
    *,
    workspace_root: Path,
    state_root: Path,
    candidate_admission: str | None,
) -> dict[str, Any]:
    """Run one bounded Case Desk update through accepted Windows mechanics.

    The caller supplies only the user-level case id, note and reviewed status.
    PID/window/session paths come from one fixed externally prepared session
    descriptor outside Chat FilesRoot. The procedure never reads fixture state
    or mutation audit files; those remain reserved for the independent L3
    Finish Gate.
    """

    started = time.monotonic()
    workspace_root = workspace_root.resolve()
    state_root = state_root.resolve()
    if not workspace_root.is_dir():
        raise ValueError("configured workspace root is not an existing directory")
    if candidate_admission != QUALIFICATION_ADMISSION:
        raise PermissionError("Windows case procedure is not admitted by this profile")

    session = _load_active_session()
    case_id, note, requested_status = _validate_request(request, run_id=session["run_id"])
    task_id = secrets.token_hex(16)
    note_sha256 = _sha256_text(note)
    task_state: dict[str, Any] = {
        "schema_version": 1,
        "task_id": task_id,
        "procedure_id": PROCEDURE_ID,
        "procedure_version": PROCEDURE_VERSION,
        "procedure_status": PROCEDURE_STATUS,
        "active_run_id": session["run_id"],
        "expected_head": session["expected_head"],
        "case_id": case_id,
        "note_sha256": note_sha256,
        "requested_status": requested_status,
        "current_node": "preflight",
        "status": "running",
        "action_count": 0,
        "action_budget": MAX_ACTIONS,
        "runtime_budget_seconds": MAX_RUNTIME_SECONDS,
        "transition_receipts": [],
        "working_state": None,
        "finish_gate": None,
        "escalation_reason": None,
        "created_at": _utc_now(),
    }
    _write_checkpoint(state_root, task_state)

    server = None
    thread: threading.Thread | None = None
    backend = None
    resolver = None
    observation_stream = WindowsDesktopObservationStream(
        subject=f"{PROCEDURE_ID}:{task_id}",
        stream_id=f"{task_id}:windows-desktop",
    )
    working_state: WorkingState | None = None

    def checkpoint() -> None:
        _write_checkpoint(state_root, task_state)

    def ensure_budget() -> None:
        if int(task_state["action_count"]) >= MAX_ACTIONS:
            raise ProcedureAbstained("action_budget_exhausted")
        if time.monotonic() - started >= MAX_RUNTIME_SECONDS:
            raise ProcedureAbstained("runtime_budget_exhausted")

    def observe_raw() -> dict[str, Any]:
        from runtime.windows.observation import observe_bound_window

        assert resolver is not None
        return observe_bound_window(resolver, session["window_name"]).to_mapping()

    def observe_bound() -> tuple[dict[str, Any], ObservationSnapshot]:
        raw = observe_raw()
        return raw, observation_stream.observe(raw)

    try:
        # Imported lazily so CI and non-Windows semantic inventory checks do not
        # gain an OpenAdapt dependency merely by importing the Control Plane.
        from openadapt_flow.backend import StructuralResolutionRefused
        from openadapt_flow.backends.win_agent.server import AgentConfig, create_server
        from openadapt_flow.backends.windows_backend import WindowsBackend
        from openadapt_flow.ir import StructuralLocator

        from runtime.windows.actuation import bounded_input
        from runtime.windows.window_scoped_uia import WindowScopedUiaResolver

        resolver = WindowScopedUiaResolver()
        resolver.set_expected_process_id(int(session["fixture_pid"]))

        token = secrets.token_urlsafe(32)
        config = AgentConfig(host="127.0.0.1", port=0, token=token, allow_legacy_exec=False)
        server = create_server(config, input_fn=bounded_input, uia_fn=resolver.perform)
        host, port = server.server_address[:2]
        if str(host) != "127.0.0.1" or int(port) <= 0:
            raise ProcedureAbstained("windows_executor_not_loopback_bound")
        thread = threading.Thread(
            target=server.serve_forever,
            name=f"{PROCEDURE_ID}-{task_id[:8]}",
            daemon=True,
        )
        thread.start()
        base_url = f"http://127.0.0.1:{int(port)}"
        with urllib.request.urlopen(f"{base_url}/health", timeout=5.0) as response:
            health = json.loads(response.read(64_000).decode("utf-8"))
        if health.get("auth_required") is not True or "legacy_exec" in (health.get("capabilities") or []):
            raise ProcedureAbstained("windows_executor_security_contract_failed")

        backend = WindowsBackend(
            server_url=base_url,
            auth_token=token,
            require_tls=False,
            allow_legacy_exec=False,
        )
        if bool(getattr(backend, "_allow_legacy_exec", True)):
            raise ProcedureAbstained("windows_backend_legacy_exec_enabled")

        def structural(role: str, name: str) -> Any:
            return StructuralLocator(role=role, name=name, window_name=session["window_name"])

        def resolve_unique(role: str, name: str) -> Any:
            assert backend is not None
            locator = structural(role, name)
            handle = backend.locate_structural(locator)
            if handle is None or handle.candidate_count != 1 or not handle.target_fingerprint:
                raise ProcedureAbstained(f"uia_target_not_unique:{role}:{name}")
            return locator, handle

        def act_native(role: str, name: str) -> dict[str, Any]:
            assert backend is not None
            locator, handle = resolve_unique(role, name)
            receipt = backend.act_structural(locator, handle)
            mapped = _receipt_mapping(receipt)
            if (
                not mapped["native"]
                or mapped["outcome_verified"] is not False
                or mapped["target_fingerprint"] != handle.target_fingerprint
            ):
                raise ProcedureAbstained(f"uia_delivery_contract_failed:{role}:{name}")
            return mapped

        def guarded_coordinate(role: str, name: str) -> dict[str, Any]:
            assert backend is not None
            last: Exception | None = None
            for _ in range(12):
                _locator, handle = resolve_unique(role, name)
                point = (int(handle.point[0]), int(handle.point[1]))
                try:
                    backend.arm_guarded_coordinate(*point)
                    frame = backend.screenshot()
                    receipt = backend.act_guarded_coordinate(
                        *point,
                        expected_frame_sha256=hashlib.sha256(frame).hexdigest(),
                    )
                    mapped = _receipt_mapping(receipt)
                    if mapped["operation"] != "physical_click" or mapped["outcome_verified"] is not False:
                        raise ProcedureAbstained("guarded_coordinate_delivery_contract_failed")
                    return mapped
                except StructuralResolutionRefused as exc:
                    last = exc
                    backend.cancel_guarded_coordinate()
                    time.sleep(0.06)
            raise ProcedureAbstained("guarded_coordinate_never_stabilized") from last

        def guarded_type(text: str, role: str, name: str) -> dict[str, Any]:
            assert backend is not None
            last: Exception | None = None
            for _ in range(12):
                _locator, handle = resolve_unique(role, name)
                point = (int(handle.point[0]), int(handle.point[1]))
                try:
                    backend.arm_guarded_keyboard(*point)
                    frame = backend.guarded_keyboard_frame()
                    receipt = backend.type_text_guarded(
                        text,
                        expected_frame_sha256=hashlib.sha256(frame).hexdigest(),
                    )
                    mapped = _receipt_mapping(receipt)
                    if mapped["operation"] != "physical_type_text" or mapped["outcome_verified"] is not False:
                        raise ProcedureAbstained("guarded_text_delivery_contract_failed")
                    return mapped
                except StructuralResolutionRefused as exc:
                    last = exc
                    backend.cancel_guarded_keyboard()
                    time.sleep(0.06)
            raise ProcedureAbstained("guarded_text_never_stabilized") from last

        def run_transition(
            *,
            transition_id: str,
            from_node: str,
            to_node: str,
            before_snapshot: ObservationSnapshot,
            expected: dict[str, Any],
            deliver_fn: Callable[[], dict[str, Any]],
            failure_reason: str,
            evidence_batch_id: str | None = None,
        ) -> tuple[dict[str, Any], ObservationSnapshot, dict[str, Any]]:
            nonlocal working_state

            if working_state is None:
                raise RuntimeError("Windows WorkingState is not initialized")
            ensure_budget()
            intent = _windows_case_intent(
                working_state,
                task_id=task_id,
                transition_id=transition_id,
                run_id=session["run_id"],
                expected_head=session["expected_head"],
                case_id=case_id,
                note_sha256=note_sha256,
                requested_status=requested_status,
            )
            decision = _windows_case_guard_decision(
                working_state,
                intent,
                transition_id=transition_id,
                task_id=task_id,
                run_id=session["run_id"],
                expected_head=session["expected_head"],
                case_id=case_id,
                note_sha256=note_sha256,
                requested_status=requested_status,
            )
            if not decision.allowed:
                code = decision.failure.code if decision.failure is not None else "blocked"
                raise ProcedureAbstained(f"core_authorization_blocked:{transition_id}:{code}")

            delivery_error: Exception | None = None
            try:
                delivery = deliver_fn()
            except Exception as exc:
                delivery_error = exc
                delivery = {
                    "operation": "delivery_error",
                    "native": False,
                    "outcome_verified": False,
                    "target_fingerprint": None,
                    "error": type(exc).__name__,
                }
            task_state["action_count"] += 1

            try:
                observed, verification, settle = _settle_postcondition(
                    observe_bound,
                    lambda pair: _verification(
                        before=before_snapshot,
                        after=pair[1],
                        expected=expected,
                        evidence_batch_id=evidence_batch_id,
                    ),
                )
            except Exception as exc:
                working_state = _record_windows_case_attempt(
                    working_state,
                    intent,
                    MutatingOutcome.OUTCOME_UNKNOWN,
                    _windows_unknown_failure(intent),
                    transition_id=transition_id,
                    task_id=task_id,
                    run_id=session["run_id"],
                    expected_head=session["expected_head"],
                    case_id=case_id,
                    note_sha256=note_sha256,
                    requested_status=requested_status,
                )
                task_state["working_state"] = working_state.as_dict()
                checkpoint()
                raise ProcedureAbstained(
                    f"{transition_id}_verification_unavailable:{type(exc).__name__}"
                ) from exc

            after_raw, after_snapshot = observed
            if verification["status"] == VerificationStatus.PASS.value:
                outcome = MutatingOutcome.VERIFIED_APPLIED
                failure = None
            else:
                outcome = MutatingOutcome.OUTCOME_UNKNOWN
                failure = _windows_unknown_failure(intent)

            working_state = _record_windows_case_attempt(
                working_state,
                intent,
                outcome,
                failure,
                transition_id=transition_id,
                task_id=task_id,
                run_id=session["run_id"],
                expected_head=session["expected_head"],
                case_id=case_id,
                note_sha256=note_sha256,
                requested_status=requested_status,
            )
            working_state = working_state.record_observation(
                after_snapshot.ref,
                expected_revision=working_state.revision,
            )
            task_state["working_state"] = working_state.as_dict()
            _record_transition(
                task_state,
                transition_id=transition_id,
                from_node=from_node,
                to_node=to_node,
                delivery=delivery,
                verification=verification,
                postcondition_observation=settle,
            )
            checkpoint()

            if delivery_error is not None:
                raise ProcedureAbstained(
                    f"{transition_id}_delivery_uncertain:{type(delivery_error).__name__}"
                ) from delivery_error
            if verification["status"] != VerificationStatus.PASS.value:
                raise ProcedureAbstained(failure_reason)
            return after_raw, after_snapshot, verification

        initial, initial_snapshot = observe_bound()
        initial_token = _extract_state_token(initial["visible_text"])
        expected_initial = _state_token(
            selected="NONE", status="NONE", note_sha256=_EMPTY_SHA256, saved=0
        )
        if initial_token != expected_initial:
            raise ProcedureAbstained("case_desk_not_in_clean_preflight_state")
        _initial_status, initial_note_count, _ = _extract_case_summary(initial["visible_text"], case_id)

        working_state = _new_windows_working_state(
            task_id=task_id,
            initial=initial_snapshot,
            run_id=session["run_id"],
            expected_head=session["expected_head"],
            case_id=case_id,
            note_sha256=note_sha256,
            requested_status=requested_status,
        )
        task_state["working_state"] = working_state.as_dict()
        checkpoint()

        selected_token = _state_token(
            selected=case_id, status="NONE", note_sha256=_EMPTY_SHA256, saved=0
        )
        selected_visible = _replace_visible_lines(initial["visible_text"], {initial_token: selected_token})
        selected, selected_snapshot, selected_result = run_transition(
            transition_id="select_case",
            from_node="preflight",
            to_node="case_selected",
            before_snapshot=initial_snapshot,
            expected={"evidence": {"visible_text_sha256": _sha256_text(selected_visible)}},
            deliver_fn=lambda: guarded_coordinate("listitem", case_id),
            failure_reason="select_case_postcondition_not_verified",
        )

        note_control = _control_fingerprint(
            selected,
            role="textbox",
            name="New case note",
            focused=True,
        )
        focused, focused_snapshot, focus_result = run_transition(
            transition_id="focus_note",
            from_node="case_selected",
            to_node="note_focused",
            before_snapshot=selected_snapshot,
            expected={"window": {"focused_control": note_control}},
            deliver_fn=lambda: act_native("textbox", "New case note"),
            failure_reason="focus_note_postcondition_not_verified",
        )

        note_token = _state_token(
            selected=case_id, status="NONE", note_sha256=note_sha256, saved=0
        )
        note_visible = _replace_visible_lines(focused["visible_text"], {selected_token: note_token})
        noted, noted_snapshot, note_result = run_transition(
            transition_id="enter_note",
            from_node="note_focused",
            to_node="note_entered",
            before_snapshot=focused_snapshot,
            expected={"evidence": {"visible_text_sha256": _sha256_text(note_visible)}},
            deliver_fn=lambda: guarded_type(note, "textbox", "New case note"),
            failure_reason="enter_note_postcondition_not_verified",
        )

        status_token = _state_token(
            selected=case_id, status=requested_status, note_sha256=note_sha256, saved=0
        )
        status_visible = _replace_visible_lines(noted["visible_text"], {note_token: status_token})
        status_set, status_snapshot, status_result = run_transition(
            transition_id="set_status",
            from_node="note_entered",
            to_node="status_set",
            before_snapshot=noted_snapshot,
            expected={"evidence": {"visible_text_sha256": _sha256_text(status_visible)}},
            deliver_fn=lambda: act_native("button", f"Set status {requested_status}"),
            failure_reason="set_status_postcondition_not_verified",
        )

        _current_status, current_note_count, summary_before = _extract_case_summary(
            status_set["visible_text"], case_id
        )
        if current_note_count != initial_note_count:
            raise ProcedureAbstained("target_case_changed_before_save")
        summary_after = f"CASESTATE|id={case_id}|status={requested_status}|notes={initial_note_count + 1}"
        saved_token = _state_token(
            selected=case_id, status=requested_status, note_sha256=note_sha256, saved=1
        )
        saved_visible = _replace_visible_lines(
            status_set["visible_text"],
            {status_token: saved_token, summary_before: summary_after},
        )
        evidence_batch_id = f"{task_id}:completion:{task_state['action_count'] + 1}"
        saved, saved_snapshot, save_result = run_transition(
            transition_id="save_case",
            from_node="status_set",
            to_node="saved_verified",
            before_snapshot=status_snapshot,
            expected={"evidence": {"visible_text_sha256": _sha256_text(saved_visible)}},
            deliver_fn=lambda: act_native("button", "Save case"),
            failure_reason="save_case_postcondition_not_verified",
            evidence_batch_id=evidence_batch_id,
        )
        safety_result = _verification(
            before=status_snapshot,
            after=saved_snapshot,
            expected={"evidence": {"visible_text_sha256": _sha256_text(saved_visible)}},
            evidence_batch_id=evidence_batch_id,
        )
        finish_gate = evaluate_finish_gate(
            evidence_batch_id=evidence_batch_id,
            candidate_done=True,
            goal_results=(),
            safety_results=(),
            unresolved=("external_l3_finish_gate_required",),
        )
        task_state["finish_gate"] = {
            **finish_gate.as_dict(),
            "local_goal_verification": _kernel_receipt(save_result),
            "local_safety_verification": _kernel_receipt(safety_result),
        }
        checkpoint()
        if safety_result["status"] != VerificationStatus.PASS.value:
            raise ProcedureAbstained("save_case_safety_postcondition_not_verified")

        task_state["status"] = "completed"
        task_state["current_node"] = "bounded_execution_completed"
        task_state["completed_at"] = _utc_now()
        checkpoint()
        return _result(
            task_state,
            active_run_id=session["run_id"],
            case_id=case_id,
            requested_status=requested_status,
            note_sha256=note_sha256,
            source_head=session["expected_head"],
            local_execution_verified=True,
            external_finish_gate_required=True,
            executor_security={
                "loopback": True,
                "auth_required": True,
                "legacy_exec_enabled": False,
                "backend_legacy_exec_enabled": False,
            },
            resolver_stats=vars(resolver.stats).copy(),
        )
    except ProcedureAbstained as exc:
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = str(exc)
        task_state["finished_at"] = _utc_now()
        checkpoint()
    except Exception as exc:
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = f"runtime_uncertain:{type(exc).__name__}"
        task_state["finished_at"] = _utc_now()
        checkpoint()
    finally:
        if server is not None:
            try:
                server.shutdown()
            except Exception:
                pass
            try:
                server.server_close()
            except Exception:
                pass
        if thread is not None:
            thread.join(timeout=5.0)

    return _result(
        task_state,
        active_run_id=session["run_id"],
        case_id=case_id,
        requested_status=requested_status,
        note_sha256=note_sha256,
        source_head=session["expected_head"],
        local_execution_verified=False,
        external_finish_gate_required=True,
        resolver_stats=(vars(resolver.stats).copy() if resolver is not None else None),
    )
