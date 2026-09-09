from __future__ import annotations

import argparse
from collections import deque
import hashlib
import hmac
import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from runtime.agent_sessions import chatgpt_temporary
from runtime.agent_sessions import chatgpt_temporary_controller as legacy
from runtime.control_plane.delegation_state import DelegationStateError


AUTH_VERSION = "1"
AUTH_DOMAIN = "CAP_AGENT_LOOPBACK_AUTH_V1"
AUTH_VERSION_HEADER = "X-CAP-Agent-Auth-Version"
AUTH_NONCE_HEADER = "X-CAP-Agent-Auth-Nonce"
AUTH_MAC_HEADER = "X-CAP-Agent-Auth-Mac"
MAX_SEEN_NONCES = 2048
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _hex64(value: Any, label: str) -> str:
    if type(value) is not str or _HEX64_RE.fullmatch(value) is None:
        raise ValueError(f"invalid {label}")
    return value


def _sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _request_auth_input(method: str, path: str, nonce: str, body: bytes) -> bytes:
    return "\n".join(
        (
            AUTH_DOMAIN,
            "request",
            method.upper(),
            path,
            nonce,
            _sha256_hex(body),
        )
    ).encode("utf-8")


def _response_auth_input(method: str, path: str, nonce: str, status: int, body: bytes) -> bytes:
    return "\n".join(
        (
            AUTH_DOMAIN,
            "response",
            method.upper(),
            path,
            nonce,
            str(status),
            _sha256_hex(body),
        )
    ).encode("utf-8")


def _mac_hex(secret_hex: str, value: bytes) -> str:
    key = bytes.fromhex(_hex64(secret_hex, "authentication secret"))
    return hmac.new(key, value, hashlib.sha256).hexdigest()


class _ReplayWindow:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._seen: set[str] = set()
        self._order: deque[str] = deque()

    def accept(self, nonce: str) -> bool:
        with self._lock:
            if nonce in self._seen:
                return False
            self._seen.add(nonce)
            self._order.append(nonce)
            while len(self._order) > MAX_SEEN_NONCES:
                expired = self._order.popleft()
                self._seen.discard(expired)
            return True


class _UnreachableBeforeRuntimeHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        self.send_error(503)

    def do_POST(self) -> None:
        self.send_error(503)


def make_authenticated_handler(runtime: legacy.TemporaryControllerRuntime):
    base_handler = legacy.make_handler(runtime)
    replay_window = _ReplayWindow()

    class Handler(base_handler):
        server_version = "CAPChatGPTTemporaryAuthenticatedAdapter/1"

        def _write_authenticated_json(
            self,
            status: int,
            value: Mapping[str, Any],
            *,
            secret: str,
            nonce: str,
        ) -> None:
            body = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
            mac = _mac_hex(
                secret,
                _response_auth_input(self.command, self.path, nonce, status, body),
            )
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header(AUTH_VERSION_HEADER, AUTH_VERSION)
            self.send_header(AUTH_NONCE_HEADER, nonce)
            self.send_header(AUTH_MAC_HEADER, mac)
            self.end_headers()
            self.wfile.write(body)

        def _read_body_bytes(self) -> bytes | None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._write_json(400, {"status": "invalid_length"})
                return None
            if length < 1 or length > legacy.MAX_BODY_BYTES:
                self._write_json(413, {"status": "invalid_size"})
                return None
            return self.rfile.read(length)

        def _authenticate_request(self, *, secret: str, body: bytes) -> str | None:
            if self.headers.get(AUTH_VERSION_HEADER) != AUTH_VERSION:
                return None
            nonce = self.headers.get(AUTH_NONCE_HEADER, "")
            supplied_mac = self.headers.get(AUTH_MAC_HEADER, "")
            if _HEX64_RE.fullmatch(nonce) is None or _HEX64_RE.fullmatch(supplied_mac) is None:
                return None
            expected = _mac_hex(
                secret,
                _request_auth_input(self.command, self.path, nonce, body),
            )
            if not hmac.compare_digest(expected, supplied_mac):
                return None
            if not replay_window.accept(nonce):
                return None
            return nonce

        def _parse_authenticated_json(self, raw: bytes) -> dict[str, Any] | None:
            try:
                value = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return None
            return value if type(value) is dict else None

        def _wire_body_has_private_capability(self, value: Mapping[str, Any]) -> bool:
            if "preflight_id" in value or "run_id" in value:
                return True
            child = value.get("child_evidence")
            return type(child) is dict and "run_id" in child

        def do_GET(self) -> None:
            if self.path == "/health":
                self._write_json(200, runtime.health())
                return
            if self.path != "/status":
                self._write_json(404, {"status": "not_found"})
                return
            try:
                state = runtime.require_state()
            except DelegationStateError as exc:
                self._write_json(409, {"status": "rejected", "reason": str(exc)})
                return
            secret = state.token
            nonce = self._authenticate_request(secret=secret, body=b"")
            if nonce is None:
                self._write_json(403, {"status": "forbidden"})
                return
            try:
                value = state.status()
                self._write_authenticated_json(200, value, secret=secret, nonce=nonce)
            except DelegationStateError as exc:
                self._write_authenticated_json(
                    409,
                    {"status": "rejected", "reason": str(exc)[:512]},
                    secret=secret,
                    nonce=nonce,
                )

        def do_POST(self) -> None:
            preflight_path = self.path in {"/preflight", "/preflight-commit"}
            if preflight_path:
                secret = runtime.preflight_id
                if secret is None:
                    self._write_json(403, {"status": "forbidden"})
                    return
                state = None
            else:
                try:
                    state = runtime.require_state()
                except DelegationStateError as exc:
                    self._write_json(409, {"status": "rejected", "reason": str(exc)})
                    return
                secret = state.token

            raw = self._read_body_bytes()
            if raw is None:
                return
            nonce = self._authenticate_request(secret=secret, body=raw)
            if nonce is None:
                self._write_json(403, {"status": "forbidden"})
                return
            value = self._parse_authenticated_json(raw)
            if value is None:
                self._write_authenticated_json(
                    409,
                    {"status": "rejected", "reason": "invalid JSON request"},
                    secret=secret,
                    nonce=nonce,
                )
                return
            if self._wire_body_has_private_capability(value):
                self._write_authenticated_json(
                    409,
                    {"status": "rejected", "reason": "private capability must not cross loopback wire"},
                    secret=secret,
                    nonce=nonce,
                )
                return

            if preflight_path:
                value["preflight_id"] = secret
                operation = runtime.prepare_live_handoff if self.path == "/preflight" else runtime.commit_live_handoff
            else:
                value["run_id"] = secret
                if self.path == "/authorize-send":
                    child = value.get("child_evidence")
                    if type(child) is not dict:
                        self._write_authenticated_json(
                            409,
                            {"status": "rejected", "reason": "child evidence must be an object"},
                            secret=secret,
                            nonce=nonce,
                        )
                        return
                    value["child_evidence"] = {**child, "run_id": secret}
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
                    self._write_authenticated_json(
                        404,
                        {"status": "not_found"},
                        secret=secret,
                        nonce=nonce,
                    )
                    return

            try:
                result = operation(value)
                self._write_authenticated_json(
                    200,
                    result or {"schema_version": 1, "status": "recorded"},
                    secret=secret,
                    nonce=nonce,
                )
            except (DelegationStateError, ValueError, OSError) as exc:
                self._write_authenticated_json(
                    409,
                    {"status": "rejected", "reason": str(exc)[:512]},
                    secret=secret,
                    nonce=nonce,
                )

    return Handler


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Authenticated bounded ChatGPT Temporary worker adapter controller")
    parser.add_argument("--identity-json", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--runtime-attestation-json", required=True)
    parser.add_argument("--state-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--port", type=int, default=chatgpt_temporary.COLLECTOR_PORT)
    parser.add_argument("--timeout-seconds", type=int, default=legacy.DEFAULT_TIMEOUT_SECONDS)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.port != chatgpt_temporary.COLLECTOR_PORT:
        raise SystemExit(f"adapter is pinned to loopback port {chatgpt_temporary.COLLECTOR_PORT}")
    if not 60 <= args.timeout_seconds <= 7200:
        raise SystemExit("invalid timeout")

    identity_path = Path(args.identity_json).resolve()
    task_path = Path(args.task_file).resolve()
    runtime_attestation_path = Path(args.runtime_attestation_json).resolve()
    identity_value = legacy._load_json_file(identity_path, "identity")
    expected_runtime_attestation_value = legacy._load_json_file(
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

    # Bind and listen before constructing TemporaryControllerRuntime. Runtime
    # construction may publish preflight.json, so a pre-bound rogue listener
    # must fail before any browser-visible capability exists.
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.port),
        _UnreachableBeforeRuntimeHandler,
        bind_and_activate=False,
    )
    try:
        server.server_bind()
        server.server_activate()
    except OSError as exc:
        server.server_close()
        raise SystemExit(f"adapter loopback bind failed before preflight publication: {exc}") from exc

    try:
        runtime = legacy.TemporaryControllerRuntime(
            identity_value=identity_value,
            task=task,
            expected_runtime_attestation_value=expected_runtime_attestation_value,
            state_root=Path(args.state_root),
            output_dir=Path(args.output_dir),
        )
    except (DelegationStateError, OSError) as exc:
        server.server_close()
        raise SystemExit(f"adapter preparation failed: {exc}") from exc

    server.RequestHandlerClass = make_authenticated_handler(runtime)
    server.daemon_threads = True
    worker = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.25},
        daemon=True,
    )
    worker.start()
    phase = runtime.health()["status"]
    print(
        f"CAP_AGENT_SESSION_ADAPTER={phase} adapter={chatgpt_temporary.ADAPTER_ID} "
        f"delegation_id={runtime.preflight.delegation_id}",
        flush=True,
    )

    started = time.monotonic()
    if runtime.state is None:
        runtime.activated.wait(args.timeout_seconds)
    state = runtime.state
    if state is None:
        completed = False
    else:
        remaining = max(0.0, args.timeout_seconds - (time.monotonic() - started))
        completed = state.done.wait(remaining)
        if not completed:
            try:
                request_id = state.request_final_observation_if_delivered()
            except (DelegationStateError, OSError):
                request_id = None
            if request_id is not None:
                completed = state.done.wait(legacy.FINAL_OBSERVATION_GRACE_SECONDS)

    server.shutdown()
    server.server_close()
    worker.join(timeout=5)
    return 0 if completed else 3


if __name__ == "__main__":
    raise SystemExit(main())
