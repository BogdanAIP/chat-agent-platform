from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
from dataclasses import replace
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from runtime.agent_sessions import chatgpt_temporary, source_attestation
from runtime.control_plane.delegation_state import (
    DelegationSnapshot,
    DelegationStateError,
    load_delegation,
    parse_delegation_identity,
)


MAX_BODY_BYTES = 400_000
MAX_EVENT_DETAILS_BYTES = 32_000
MAX_EVENTS = 200
DEFAULT_TIMEOUT_SECONDS = 1800
FINAL_OBSERVATION_GRACE_SECONDS = 20
ALLOWED_EVENTS = {
    "adapter-loaded",
    "temporary-ui-not-proven",
    "browser-claim-failed",
    "browser-claim-committed",
    "local-send-authority-denied",
    "send-clicked",
    "delivery-visible",
    "delivery-ambiguous",
    "post-delivery-cleanup-complete",
    "post-delivery-cleanup-failed",
    "result-capture-failed",
    "timeout",
    "stopped",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _plain(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise DelegationStateError(f"{label} must be a plain object")
    return value


def _exact(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise DelegationStateError(
            f"{label} keys mismatch: missing={sorted(expected - actual) or 'none'} "
            f"unexpected={sorted(actual - expected) or 'none'}"
        )


def _bind_launch_provenance(
    launch: chatgpt_temporary.TemporaryLaunchIntent,
    *,
    expected_head: str,
) -> chatgpt_temporary.TemporaryLaunchIntent:
    parts = urlsplit(launch.launch_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["cap_expected_head"] = expected_head
    query["cap_prompt_sha256"] = launch.prompt_sha256
    return replace(
        launch,
        launch_url=urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(query),
                parts.fragment,
            )
        ),
    )


class TemporaryControllerState:
    def __init__(
        self,
        *,
        identity_value: Mapping[str, Any],
        task: str,
        expected_runtime_attestation_value: Mapping[str, Any],
        state_root: Path,
        output_dir: Path,
    ) -> None:
        self.identity = parse_delegation_identity(identity_value)
        self.identity_value = self.identity.as_dict()
        self.expected_runtime_attestation = source_attestation.parse_expected_runtime_attestation(
            expected_runtime_attestation_value
        )
        self.expected_runtime_digest = source_attestation.validate_runtime_attestation(
            {
                "schema_version": 1,
                "adapter_id": source_attestation.ADAPTER_ID,
                "execution_generation": self.expected_runtime_attestation.execution_generation,
                "assets": dict(self.expected_runtime_attestation.assets),
            },
            expected=self.expected_runtime_attestation,
        )
        self.state_root = state_root.resolve()
        self.output_dir = output_dir.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        prepared_launch = chatgpt_temporary.prepare_temporary_session(
            self.identity_value,
            task=task,
            state_root=self.state_root,
        )
        self.launch = _bind_launch_provenance(
            prepared_launch,
            expected_head=self.expected_runtime_attestation.expected_head,
        )
        self.token = self.launch.run_id
        self.progress_path = self.output_dir / "progress.json"
        self.result_path = self.output_dir / "result.json"
        self.launch_path = self.output_dir / "launch.json"
        self.lock = threading.Lock()
        self.done = threading.Event()
        self.events: list[dict[str, Any]] = []
        self.cleanup_token: str | None = None
        self.capture_token: str | None = None
        self.final_observation_request_id: str | None = None

        durable_snapshot = load_delegation(
            self.identity_value,
            state_root=self.state_root,
        )
        if durable_snapshot.worker_session_ref is not None:
            self._require_bound_runtime_provenance(durable_snapshot)
        terminal_snapshot = durable_snapshot if self.launch.result_state == "recorded" else None

        _atomic_json_write(
            self.launch_path,
            {
                "schema_version": 1,
                "adapter_id": chatgpt_temporary.ADAPTER_ID,
                "delegation_id": self.launch.delegation_id,
                "delivery_id": self.launch.delivery_id,
                "launch_url": self.launch.launch_url,
                "prompt_sha256": self.launch.prompt_sha256,
                "launch_now": self.launch.launch_now,
                "launch_state": self.launch.launch_state,
                "delivery_state": self.launch.delivery_state,
                "result_state": self.launch.result_state,
                "expected_runtime_head": self.expected_runtime_attestation.expected_head,
                "execution_generation": self.expected_runtime_attestation.execution_generation,
                "created_at": _utc_now(),
            },
        )
        if terminal_snapshot is not None:
            self._write_snapshot_result(terminal_snapshot)
            self.done.set()

    def _require_correlation(self, value: Mapping[str, Any], label: str) -> str:
        if value.get("schema_version") != 1:
            raise DelegationStateError(f"{label} schema mismatch")
        if value.get("run_id") != self.launch.run_id:
            raise DelegationStateError(f"{label} run correlation mismatch")
        if value.get("delegation_id") != self.launch.delegation_id:
            raise DelegationStateError(f"{label} delegation correlation mismatch")
        if value.get("delivery_id") != self.launch.delivery_id:
            raise DelegationStateError(f"{label} delivery correlation mismatch")
        return self.launch.run_id

    def _require_launch_provenance(self, value: Mapping[str, Any], label: str) -> None:
        if value.get("expected_runtime_head") != self.expected_runtime_attestation.expected_head:
            raise DelegationStateError(f"{label} expected runtime HEAD mismatch")
        if value.get("prompt_sha256") != self.launch.prompt_sha256:
            raise DelegationStateError(f"{label} launch prompt digest mismatch")

    def _validate_runtime_attestation(self, value: Any) -> str:
        report = _plain(value, "runtime attestation")
        return source_attestation.validate_runtime_attestation(
            report,
            expected=self.expected_runtime_attestation,
        )

    def _require_bound_runtime_provenance(self, snapshot: DelegationSnapshot) -> None:
        session = snapshot.worker_session_ref
        expected_suffix = f":runtime:{self.expected_runtime_digest}"
        if session is None or not session.observation_ref.endswith(expected_suffix):
            raise DelegationStateError(
                "bound worker runtime provenance does not match expected runtime attestation"
            )

    def status(self) -> dict[str, Any]:
        snapshot = load_delegation(self.identity_value, state_root=self.state_root)
        with self.lock:
            final_request_id = self.final_observation_request_id
        return {
            "schema_version": 1,
            "status": "ready",
            "adapter_id": chatgpt_temporary.ADAPTER_ID,
            "delegation_id": snapshot.delegation_id,
            "delivery_id": snapshot.delivery_id,
            "launch_state": snapshot.launch_state,
            "delivery_state": snapshot.delivery_state,
            "result_state": snapshot.result_state,
            "result_status": snapshot.result_status,
            "final_observation_request_id": final_request_id,
        }

    def record_event(self, value: Mapping[str, Any]) -> dict[str, Any]:
        event = _plain(value, "adapter event")
        _exact(
            event,
            {"schema_version", "run_id", "delegation_id", "delivery_id", "event", "details"},
            "adapter event",
        )
        self._require_correlation(event, "adapter event")
        if event["event"] not in ALLOWED_EVENTS:
            raise DelegationStateError("unsupported adapter event")
        if type(event["details"]) is not dict:
            raise DelegationStateError("adapter event details must be an object")
        if len(json.dumps(event["details"], ensure_ascii=False).encode("utf-8")) > MAX_EVENT_DETAILS_BYTES:
            raise DelegationStateError("adapter event details exceed accepted bound")

        cleanup_token = None
        details = event["details"]
        if (
            event["event"] == "delivery-visible"
            and details.get("post_delivery_ui_disarmed") is True
            and details.get("launch_url_clean") is True
            and details.get("composer_clean") is True
        ):
            snapshot = load_delegation(self.identity_value, state_root=self.state_root)
            if snapshot.delivery_state != "delivered" or snapshot.result_state != "open":
                raise DelegationStateError("cleanup acknowledgement requires delivered open delegation")
            self._require_bound_runtime_provenance(snapshot)
            cleanup_token = secrets.token_hex(32)

        with self.lock:
            if cleanup_token is not None:
                self.cleanup_token = cleanup_token
            self.events.append({**event, "received_at": _utc_now()})
            self.events = self.events[-MAX_EVENTS:]
            _atomic_json_write(
                self.progress_path,
                {
                    "schema_version": 1,
                    "adapter_id": chatgpt_temporary.ADAPTER_ID,
                    "delegation_id": self.launch.delegation_id,
                    "delivery_id": self.launch.delivery_id,
                    "events": self.events,
                    "updated_at": _utc_now(),
                },
            )
        result: dict[str, Any] = {"schema_version": 1, "status": "recorded"}
        if cleanup_token is not None:
            result["cleanup_token"] = cleanup_token
        return result

    def authorize_send(self, value: Mapping[str, Any]) -> dict[str, Any]:
        request = _plain(value, "send authority request")
        _exact(
            request,
            {
                "schema_version",
                "run_id",
                "delegation_id",
                "delivery_id",
                "expected_runtime_head",
                "prompt_sha256",
                "browser_claim_committed",
                "browser_claim_id",
                "child_evidence",
                "runtime_attestation",
            },
            "send authority request",
        )
        run_id = self._require_correlation(request, "send authority request")
        self._require_launch_provenance(request, "send authority request")
        if request["browser_claim_committed"] is not True:
            raise DelegationStateError("browser send claim is not committed")
        if request["browser_claim_id"] != self.launch.delivery_id:
            raise DelegationStateError("browser send claim id mismatch")

        runtime_digest = self._validate_runtime_attestation(request["runtime_attestation"])
        child_evidence = dict(_plain(request["child_evidence"], "temporary child evidence"))
        observation_ref = child_evidence.get("observation_ref")
        if type(observation_ref) is not str:
            raise DelegationStateError("temporary child observation_ref must be text")
        attested_ref = f"{observation_ref}:runtime:{runtime_digest}"
        if len(attested_ref) > chatgpt_temporary.MAX_EVIDENCE_REF_CHARS:
            raise DelegationStateError("attested child observation_ref exceeds accepted bound")
        child_evidence["observation_ref"] = attested_ref

        chatgpt_temporary.bind_temporary_child(
            self.identity_value,
            evidence_value=child_evidence,
            state_root=self.state_root,
        )
        claim = chatgpt_temporary.claim_temporary_delivery(
            self.identity_value,
            run_id=run_id,
            state_root=self.state_root,
        )
        return {
            "schema_version": 1,
            "status": "authorized" if claim.claimed_now else "denied",
            "send_authorized": claim.claimed_now,
            "delegation_id": claim.delegation_id,
            "delivery_id": claim.delivery_id,
            "delivery_state": claim.delivery_state,
            "runtime_attestation_sha256": runtime_digest,
        }

    def record_delivery(self, value: Mapping[str, Any]) -> dict[str, Any]:
        request = _plain(value, "delivery outcome request")
        _exact(
            request,
            {
                "schema_version",
                "run_id",
                "delegation_id",
                "delivery_id",
                "task_sha256",
                "outcome",
                "evidence_ref",
            },
            "delivery outcome request",
        )
        self._require_correlation(request, "delivery outcome request")
        snapshot = chatgpt_temporary.record_temporary_delivery(
            self.identity_value,
            evidence_value=request,
            state_root=self.state_root,
        )
        return {
            "schema_version": 1,
            "status": "recorded",
            "delivery_state": snapshot.delivery_state,
            "result_state": snapshot.result_state,
        }

    def _write_snapshot_result(self, snapshot: DelegationSnapshot) -> None:
        _atomic_json_write(
            self.result_path,
            {
                "schema_version": 1,
                "adapter_id": chatgpt_temporary.ADAPTER_ID,
                "delegation_id": snapshot.delegation_id,
                "delivery_id": snapshot.delivery_id,
                "worker_kind": snapshot.identity.worker_kind,
                "result_contract_id": snapshot.identity.result_contract_id,
                "status": snapshot.result_status,
                "payload": snapshot.result_payload,
                "payload_sha256": snapshot.result_sha256,
                "recorded_at": _utc_now(),
            },
        )

    def _record_result_text(self, *, run_id: str, result_text: Any) -> DelegationSnapshot:
        snapshot = chatgpt_temporary.record_temporary_worker_result(
            self.identity_value,
            run_id=run_id,
            result_text=result_text,
            state_root=self.state_root,
        )
        with self.lock:
            self._write_snapshot_result(snapshot)
            self.done.set()
        return snapshot

    def prepare_capture(self, value: Mapping[str, Any]) -> dict[str, Any]:
        request = _plain(value, "worker capture preparation")
        _exact(
            request,
            {
                "schema_version",
                "run_id",
                "delegation_id",
                "delivery_id",
                "cleanup_token",
                "runtime_attestation",
            },
            "worker capture preparation",
        )
        self._require_correlation(request, "worker capture preparation")
        cleanup_token = request["cleanup_token"]
        if type(cleanup_token) is not str or len(cleanup_token) != 64:
            raise DelegationStateError("worker capture cleanup token is invalid")
        with self.lock:
            if cleanup_token != self.cleanup_token:
                raise DelegationStateError("worker capture cleanup token is stale or missing")
        durable_snapshot = load_delegation(self.identity_value, state_root=self.state_root)
        self._require_bound_runtime_provenance(durable_snapshot)
        runtime_digest = self._validate_runtime_attestation(request["runtime_attestation"])
        capture_token = secrets.token_hex(32)
        with self.lock:
            self.capture_token = capture_token
        return {
            "schema_version": 1,
            "status": "capture-prepared",
            "capture_token": capture_token,
            "runtime_attestation_sha256": runtime_digest,
        }

    def record_capture(self, value: Mapping[str, Any]) -> dict[str, Any]:
        request = _plain(value, "worker capture request")
        _exact(
            request,
            {
                "schema_version",
                "run_id",
                "delegation_id",
                "delivery_id",
                "cleanup_token",
                "capture_token",
                "result_text",
            },
            "worker capture request",
        )
        run_id = self._require_correlation(request, "worker capture request")
        cleanup_token = request["cleanup_token"]
        capture_token = request["capture_token"]
        if type(cleanup_token) is not str or len(cleanup_token) != 64:
            raise DelegationStateError("worker capture cleanup token is invalid")
        if type(capture_token) is not str or len(capture_token) != 64:
            raise DelegationStateError("worker capture token is invalid")
        with self.lock:
            if cleanup_token != self.cleanup_token:
                raise DelegationStateError("worker capture cleanup token is stale or missing")
            if capture_token != self.capture_token:
                raise DelegationStateError("worker capture preparation token is stale or missing")
            self.capture_token = None
        durable_snapshot = load_delegation(self.identity_value, state_root=self.state_root)
        self._require_bound_runtime_provenance(durable_snapshot)
        snapshot = self._record_result_text(
            run_id=run_id,
            result_text=request["result_text"],
        )
        return {
            "schema_version": 1,
            "status": "recorded",
            "result_state": snapshot.result_state,
            "worker_status": snapshot.result_status,
        }

    def request_final_observation_if_delivered(self) -> str | None:
        snapshot = load_delegation(self.identity_value, state_root=self.state_root)
        if snapshot.delivery_state != "delivered" or snapshot.result_state != "open":
            return None
        self._require_bound_runtime_provenance(snapshot)
        with self.lock:
            if self.final_observation_request_id is None:
                self.final_observation_request_id = secrets.token_hex(32)
            return self.final_observation_request_id

    def record_final_observation(self, value: Mapping[str, Any]) -> dict[str, Any]:
        request = _plain(value, "final worker observation")
        _exact(
            request,
            {
                "schema_version",
                "run_id",
                "delegation_id",
                "delivery_id",
                "request_id",
                "terminal_result_visible",
                "worker_generating",
                "runtime_attestation",
            },
            "final worker observation",
        )
        run_id = self._require_correlation(request, "final worker observation")
        with self.lock:
            expected_request_id = self.final_observation_request_id
        if expected_request_id is None or request["request_id"] != expected_request_id:
            raise DelegationStateError("final worker observation request correlation mismatch")
        if type(request["terminal_result_visible"]) is not bool or type(request["worker_generating"]) is not bool:
            raise DelegationStateError("final worker observation flags must be booleans")
        snapshot = load_delegation(self.identity_value, state_root=self.state_root)
        if snapshot.delivery_state != "delivered" or snapshot.result_state != "open":
            raise DelegationStateError("final worker observation requires delivered open delegation")
        self._require_bound_runtime_provenance(snapshot)
        runtime_digest = self._validate_runtime_attestation(request["runtime_attestation"])
        if request["terminal_result_visible"] is True:
            return {
                "schema_version": 1,
                "status": "terminal-visible-awaiting-capture",
                "runtime_attestation_sha256": runtime_digest,
            }

        reason = "generating" if request["worker_generating"] is True else "no-terminal-result"
        raw = {
            "schema_version": 1,
            "delegation_id": self.launch.delegation_id,
            "delivery_id": self.launch.delivery_id,
            "worker_kind": self.identity.worker_kind,
            "result_contract_id": self.identity.result_contract_id,
            "status": "ERROR",
            "payload": f"chatgpt_temporary_timeout_after_final_observation:{reason}",
        }
        text = (
            chatgpt_temporary.RAW_RESULT_BEGIN
            + "\n"
            + json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
            + "\n"
            + chatgpt_temporary.RAW_RESULT_END
        )
        terminal = self._record_result_text(run_id=run_id, result_text=text)
        return {
            "schema_version": 1,
            "status": "recorded-timeout",
            "result_state": terminal.result_state,
            "worker_status": terminal.result_status,
            "runtime_attestation_sha256": runtime_digest,
        }


def make_handler(state: TemporaryControllerState):
    class Handler(BaseHTTPRequestHandler):
        server_version = "CAPChatGPTTemporaryAdapter/1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _write_json(self, status: int, value: Mapping[str, Any]) -> None:
            body = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/health":
                self._write_json(
                    200,
                    {
                        "schema_version": 1,
                        "status": "ready",
                        "adapter_id": chatgpt_temporary.ADAPTER_ID,
                        "delegation_id": state.launch.delegation_id,
                        "delivery_id": state.launch.delivery_id,
                    },
                )
                return
            if self.path == "/status":
                if self.headers.get("X-CAP-Agent-Token") != state.token:
                    self._write_json(403, {"status": "forbidden"})
                    return
                try:
                    self._write_json(200, state.status())
                except DelegationStateError as exc:
                    self._write_json(409, {"status": "rejected", "reason": str(exc)[:512]})
                return
            self._write_json(404, {"status": "not_found"})

        def do_POST(self) -> None:
            handlers = {
                "/event": state.record_event,
                "/authorize-send": state.authorize_send,
                "/delivery": state.record_delivery,
                "/prepare-capture": state.prepare_capture,
                "/capture": state.record_capture,
                "/final-observation": state.record_final_observation,
            }
            operation = handlers.get(self.path)
            if operation is None:
                self._write_json(404, {"status": "not_found"})
                return
            if self.headers.get("X-CAP-Agent-Token") != state.token:
                self._write_json(403, {"status": "forbidden"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._write_json(400, {"status": "invalid_length"})
                return
            if length < 1 or length > MAX_BODY_BYTES:
                self._write_json(413, {"status": "invalid_size"})
                return
            raw = self.rfile.read(length)
            try:
                value = json.loads(raw.decode("utf-8"))
                result = operation(value)
                self._write_json(200, result or {"schema_version": 1, "status": "recorded"})
            except (UnicodeDecodeError, json.JSONDecodeError, DelegationStateError, ValueError) as exc:
                self._write_json(409, {"status": "rejected", "reason": str(exc)[:512]})

    return Handler


def _load_json_file(path: Path, label: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if not raw or len(raw) > 64_000:
        raise SystemExit(f"invalid {label} size")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid {label} JSON") from exc
    if type(value) is not dict:
        raise SystemExit(f"{label} must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded ChatGPT Temporary worker adapter controller")
    parser.add_argument("--identity-json", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--runtime-attestation-json", required=True)
    parser.add_argument("--state-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--port", type=int, default=chatgpt_temporary.COLLECTOR_PORT)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    if args.port != chatgpt_temporary.COLLECTOR_PORT:
        raise SystemExit(f"adapter is pinned to loopback port {chatgpt_temporary.COLLECTOR_PORT}")
    if not 60 <= args.timeout_seconds <= 7200:
        raise SystemExit("invalid timeout")

    identity_path = Path(args.identity_json).resolve()
    task_path = Path(args.task_file).resolve()
    runtime_attestation_path = Path(args.runtime_attestation_json).resolve()
    identity_value = _load_json_file(identity_path, "identity")
    expected_runtime_attestation_value = _load_json_file(
        runtime_attestation_path,
        "runtime attestation",
    )
    task_bytes = task_path.read_bytes()
    if not task_bytes or len(task_bytes) > chatgpt_temporary.MAX_TASK_BYTES:
        raise SystemExit("invalid task size")
    try:
        task = task_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit("task must be UTF-8") from exc

    try:
        state = TemporaryControllerState(
            identity_value=identity_value,
            task=task,
            expected_runtime_attestation_value=expected_runtime_attestation_value,
            state_root=Path(args.state_root),
            output_dir=Path(args.output_dir),
        )
    except (DelegationStateError, OSError) as exc:
        raise SystemExit(f"adapter preparation failed: {exc}") from exc

    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(state))
    server.daemon_threads = True
    worker = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.25},
        daemon=True,
    )
    worker.start()
    print(
        f"CAP_AGENT_SESSION_ADAPTER=ready adapter={chatgpt_temporary.ADAPTER_ID} "
        f"delegation_id={state.launch.delegation_id} launch_now={str(state.launch.launch_now).lower()}",
        flush=True,
    )
    completed = state.done.wait(args.timeout_seconds)
    if not completed:
        try:
            request_id = state.request_final_observation_if_delivered()
        except (DelegationStateError, OSError):
            request_id = None
        if request_id is not None:
            completed = state.done.wait(FINAL_OBSERVATION_GRACE_SECONDS)
    server.shutdown()
    server.server_close()
    worker.join(timeout=5)
    return 0 if completed else 3


if __name__ == "__main__":
    raise SystemExit(main())
