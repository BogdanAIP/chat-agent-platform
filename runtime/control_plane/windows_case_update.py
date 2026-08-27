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
from typing import Any

from .verification import VerificationStatus, evaluate_finish_gate
from .windows_transition import verify_windows_desktop_transition


PROCEDURE_ID = "windows_case_update_v1"
PROCEDURE_VERSION = "1"
PROCEDURE_STATUS = "candidate"
QUALIFICATION_ADMISSION = "stage26-3b-windows-l3"
MAX_NOTE_CHARS = 512
MAX_ACTIONS = 5
MAX_RUNTIME_SECONDS = 90.0
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
    before: dict[str, Any],
    after: dict[str, Any],
    expected: dict[str, Any],
    task_id: str,
    transition_id: str,
    evidence_batch_id: str | None = None,
) -> dict[str, Any]:
    return verify_windows_desktop_transition(
        before_raw=before,
        after_raw=after,
        expected=expected,
        subject=f"{PROCEDURE_ID}:{task_id}",
        stream_id=f"{task_id}:{transition_id}",
        evidence_batch_id=evidence_batch_id,
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
) -> None:
    task_state["transition_receipts"].append(
        {
            "transition_id": transition_id,
            "from_node": from_node,
            "to_node": to_node,
            "delivery": delivery,
            "kernel_verification": _kernel_receipt(verification),
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
    task_state: dict[str, Any] = {
        "schema_version": 1,
        "task_id": task_id,
        "procedure_id": PROCEDURE_ID,
        "procedure_version": PROCEDURE_VERSION,
        "procedure_status": PROCEDURE_STATUS,
        "active_run_id": session["run_id"],
        "expected_head": session["expected_head"],
        "case_id": case_id,
        "note_sha256": _sha256_text(note),
        "requested_status": requested_status,
        "current_node": "preflight",
        "status": "running",
        "action_count": 0,
        "action_budget": MAX_ACTIONS,
        "runtime_budget_seconds": MAX_RUNTIME_SECONDS,
        "transition_receipts": [],
        "finish_gate": None,
        "escalation_reason": None,
        "created_at": _utc_now(),
    }
    _write_checkpoint(state_root, task_state)

    server = None
    thread: threading.Thread | None = None
    backend = None
    resolver = None

    def checkpoint() -> None:
        _write_checkpoint(state_root, task_state)

    def ensure_budget() -> None:
        if int(task_state["action_count"]) >= MAX_ACTIONS:
            raise ProcedureAbstained("action_budget_exhausted")
        if time.monotonic() - started >= MAX_RUNTIME_SECONDS:
            raise ProcedureAbstained("runtime_budget_exhausted")

    def observe() -> dict[str, Any]:
        from runtime.windows.observation import observe_bound_window

        assert resolver is not None
        return observe_bound_window(resolver, session["window_name"]).to_mapping()

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
            _locator, handle = resolve_unique(role, name)
            point = (int(handle.point[0]), int(handle.point[1]))
            last: Exception | None = None
            for _ in range(12):
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

        def guarded_type(text: str, point: tuple[int, int]) -> dict[str, Any]:
            assert backend is not None
            last: Exception | None = None
            for _ in range(12):
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

        initial = observe()
        initial_token = _extract_state_token(initial["visible_text"])
        expected_initial = _state_token(
            selected="NONE", status="NONE", note_sha256=_EMPTY_SHA256, saved=0
        )
        if initial_token != expected_initial:
            raise ProcedureAbstained("case_desk_not_in_clean_preflight_state")
        _initial_status, initial_note_count, _ = _extract_case_summary(initial["visible_text"], case_id)

        ensure_budget()
        selected_token = _state_token(
            selected=case_id, status="NONE", note_sha256=_EMPTY_SHA256, saved=0
        )
        selected_visible = _replace_visible_lines(initial["visible_text"], {initial_token: selected_token})
        delivery = guarded_coordinate("listitem", case_id)
        task_state["action_count"] += 1
        selected = observe()
        selected_result = _verification(
            before=initial,
            after=selected,
            expected={"evidence": {"visible_text_sha256": _sha256_text(selected_visible)}},
            task_id=task_id,
            transition_id="select_case",
        )
        _record_transition(
            task_state,
            transition_id="select_case",
            from_node="preflight",
            to_node="case_selected",
            delivery=delivery,
            verification=selected_result,
        )
        checkpoint()
        if selected_result["status"] != VerificationStatus.PASS.value:
            raise ProcedureAbstained("select_case_postcondition_not_verified")

        ensure_budget()
        note_control = _control_fingerprint(
            selected,
            role="textbox",
            name="New case note",
            focused=True,
        )
        note_locator, note_handle = resolve_unique("textbox", "New case note")
        note_point = (int(note_handle.point[0]), int(note_handle.point[1]))
        focus_receipt = backend.act_structural(note_locator, note_handle)
        delivery = _receipt_mapping(focus_receipt)
        if (
            not delivery["native"]
            or delivery["outcome_verified"] is not False
            or delivery["target_fingerprint"] != note_handle.target_fingerprint
        ):
            raise ProcedureAbstained("note_focus_delivery_contract_failed")
        task_state["action_count"] += 1
        focused = observe()
        focus_result = _verification(
            before=selected,
            after=focused,
            expected={"window": {"focused_control": note_control}},
            task_id=task_id,
            transition_id="focus_note",
        )
        _record_transition(
            task_state,
            transition_id="focus_note",
            from_node="case_selected",
            to_node="note_focused",
            delivery=delivery,
            verification=focus_result,
        )
        checkpoint()
        if focus_result["status"] != VerificationStatus.PASS.value:
            raise ProcedureAbstained("focus_note_postcondition_not_verified")

        ensure_budget()
        note_token = _state_token(
            selected=case_id, status="NONE", note_sha256=_sha256_text(note), saved=0
        )
        note_visible = _replace_visible_lines(focused["visible_text"], {selected_token: note_token})
        delivery = guarded_type(note, note_point)
        task_state["action_count"] += 1
        noted = observe()
        note_result = _verification(
            before=focused,
            after=noted,
            expected={"evidence": {"visible_text_sha256": _sha256_text(note_visible)}},
            task_id=task_id,
            transition_id="enter_note",
        )
        _record_transition(
            task_state,
            transition_id="enter_note",
            from_node="note_focused",
            to_node="note_entered",
            delivery=delivery,
            verification=note_result,
        )
        checkpoint()
        if note_result["status"] != VerificationStatus.PASS.value:
            raise ProcedureAbstained("enter_note_postcondition_not_verified")

        ensure_budget()
        status_token = _state_token(
            selected=case_id, status=requested_status, note_sha256=_sha256_text(note), saved=0
        )
        status_visible = _replace_visible_lines(noted["visible_text"], {note_token: status_token})
        delivery = act_native("button", f"Set status {requested_status}")
        task_state["action_count"] += 1
        status_set = observe()
        status_result = _verification(
            before=noted,
            after=status_set,
            expected={"evidence": {"visible_text_sha256": _sha256_text(status_visible)}},
            task_id=task_id,
            transition_id="set_status",
        )
        _record_transition(
            task_state,
            transition_id="set_status",
            from_node="note_entered",
            to_node="status_set",
            delivery=delivery,
            verification=status_result,
        )
        checkpoint()
        if status_result["status"] != VerificationStatus.PASS.value:
            raise ProcedureAbstained("set_status_postcondition_not_verified")

        ensure_budget()
        _current_status, current_note_count, summary_before = _extract_case_summary(
            status_set["visible_text"], case_id
        )
        if current_note_count != initial_note_count:
            raise ProcedureAbstained("target_case_changed_before_save")
        summary_after = f"CASESTATE|id={case_id}|status={requested_status}|notes={initial_note_count + 1}"
        saved_token = _state_token(
            selected=case_id, status=requested_status, note_sha256=_sha256_text(note), saved=1
        )
        saved_visible = _replace_visible_lines(
            status_set["visible_text"],
            {status_token: saved_token, summary_before: summary_after},
        )
        delivery = act_native("button", "Save case")
        task_state["action_count"] += 1
        saved = observe()
        evidence_batch_id = f"{task_id}:completion:{task_state['action_count']}"
        save_result = _verification(
            before=status_set,
            after=saved,
            expected={"evidence": {"visible_text_sha256": _sha256_text(saved_visible)}},
            task_id=task_id,
            transition_id="save_case",
            evidence_batch_id=evidence_batch_id,
        )
        safety_result = _verification(
            before=status_set,
            after=saved,
            expected={"evidence": {"visible_text_sha256": _sha256_text(saved_visible)}},
            task_id=task_id,
            transition_id="save_case_safety",
            evidence_batch_id=evidence_batch_id,
        )
        finish_gate = evaluate_finish_gate(
            evidence_batch_id=evidence_batch_id,
            candidate_done=True,
            goal_results=(),
            safety_results=(),
            unresolved=("external_l3_finish_gate_required",),
        )
        _record_transition(
            task_state,
            transition_id="save_case",
            from_node="status_set",
            to_node="saved_verified",
            delivery=delivery,
            verification=save_result,
        )
        task_state["finish_gate"] = {
            **finish_gate.as_dict(),
            "local_goal_verification": _kernel_receipt(save_result),
            "local_safety_verification": _kernel_receipt(safety_result),
        }
        checkpoint()
        if (
            save_result["status"] != VerificationStatus.PASS.value
            or safety_result["status"] != VerificationStatus.PASS.value
        ):
            raise ProcedureAbstained("save_case_postcondition_not_verified")

        task_state["status"] = "completed"
        task_state["current_node"] = "bounded_execution_completed"
        task_state["completed_at"] = _utc_now()
        checkpoint()
        return _result(
            task_state,
            active_run_id=session["run_id"],
            case_id=case_id,
            requested_status=requested_status,
            note_sha256=_sha256_text(note),
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
        note_sha256=_sha256_text(note),
        source_head=session["expected_head"],
        local_execution_verified=False,
        external_finish_gate_required=True,
        resolver_stats=(vars(resolver.stats).copy() if resolver is not None else None),
    )
