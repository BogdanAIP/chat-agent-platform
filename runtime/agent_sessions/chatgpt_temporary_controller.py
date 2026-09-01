from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from runtime.agent_sessions import chatgpt_temporary
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
ALLOWED_EVENTS = {
    "adapter-loaded",
    "temporary-ui-not-proven",
    "browser-claim-failed",
    "browser-claim-committed",
    "local-send-authority-denied",
    "send-clicked",
    "delivery-visible",
    "delivery-ambiguous",
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


class TemporaryControllerState:
    def __init__(
        self,
        *,
        identity_value: Mapping[str, Any],
        task: str,
        state_root: Path,
        output_dir: Path,
    ) -> None:
        self.identity = parse_delegation_identity(identity_value)
        self.identity_value = self.identity.as_dict()
        self.state_root = state_root.resolve()
        self.output_dir = output_dir.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.launch = chatgpt_temporary.prepare_temporary_session(
            self.identity_value,
            task=task,
            state_root=self.state_root,
        )
        # The durable private delegation run capability also authenticates the
        # adapter-local loopback. No second ephemeral secret is introduced, so
        # a restarted controller can reconnect to the already-open child.
        self.token = self.launch.run_id
        self.progress_path = self.output_dir / "progress.json"
        self.result_path = self.output_dir / "result.json"
        self.launch_path = self.output_dir / "launch.json"
        self.lock = threading.Lock()
        self.done = threading.Event()
        self.events: list[dict[str, Any]] = []
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
                "created_at": _utc_now(),
            },
        )
        if self.launch.result_state == "recorded":
            self._write_snapshot_result(
                load_delegation(self.identity_value, state_root=self.state_root)
            )
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

    def status(self) -> dict[str, Any]:
        snapshot = load_delegation(self.identity_value, state_root=self.state_root)
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
        }

    def record_event(self, value: Mapping[str, Any]) -> None:
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
        with self.lock:
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

    def authorize_send(self, value: Mapping[str, Any]) -> dict[str, Any]:
        request = _plain(value, "send authority request")
        _exact(
            request,
            {
                "schema_version",
                "run_id",
                "delegation_id",
                "delivery_id",
                "browser_claim_committed",
                "browser_claim_id",
                "child_evidence",
            },
            "send authority request",
        )
        run_id = self._require_correlation(request, "send authority request")
        if request["browser_claim_committed"] is not True:
            raise DelegationStateError("browser send claim is not committed")
        if request["browser_claim_id"] != self.launch.delivery_id:
            raise DelegationStateError("browser send claim id mismatch")

        chatgpt_temporary.bind_temporary_child(
            self.identity_value,
            evidence_value=request["child_evidence"],
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

    def record_capture(self, value: Mapping[str, Any]) -> dict[str, Any]:
        request = _plain(value, "worker capture request")
        _exact(
            request,
            {"schema_version", "run_id", "delegation_id", "delivery_id", "result_text"},
            "worker capture request",
        )
        run_id = self._require_correlation(request, "worker capture request")
        result_text = request["result_text"]
        snapshot = chatgpt_temporary.record_temporary_worker_result(
            self.identity_value,
            run_id=run_id,
            result_text=result_text,
            state_root=self.state_root,
        )
        with self.lock:
            self._write_snapshot_result(snapshot)
            self.done.set()
        return {
            "schema_version": 1,
            "status": "recorded",
            "result_state": snapshot.result_state,
            "worker_status": snapshot.result_status,
        }

    def record_timeout_if_delivered(self) -> bool:
        snapshot = load_delegation(self.identity_value, state_root=self.state_root)
        if snapshot.delivery_state != "delivered" or snapshot.result_state != "open":
            return False
        raw = {
            "schema_version": 1,
            "delegation_id": self.launch.delegation_id,
            "delivery_id": self.launch.delivery_id,
            "worker_kind": self.identity.worker_kind,
            "result_contract_id": self.identity.result_contract_id,
            "status": "ERROR",
            "payload": "chatgpt_temporary_timeout_without_terminal_worker_result",
        }
        text = (
            chatgpt_temporary.RAW_RESULT_BEGIN
            + "\n"
            + json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
            + "\n"
            + chatgpt_temporary.RAW_RESULT_END
        )
        self.record_capture(
            {
                "schema_version": 1,
                "run_id": self.launch.run_id,
                "delegation_id": self.launch.delegation_id,
                "delivery_id": self.launch.delivery_id,
                "result_text": text,
            }
        )
        return True


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
                "/capture": state.record_capture,
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
    identity_value = _load_json_file(identity_path, "identity")
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
            completed = state.record_timeout_if_delivered()
        except (DelegationStateError, OSError):
            completed = False
    server.shutdown()
    server.server_close()
    worker.join(timeout=5)
    return 0 if completed else 3


if __name__ == "__main__":
    raise SystemExit(main())
