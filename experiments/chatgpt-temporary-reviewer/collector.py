from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

RUN_ID_RE = re.compile(r"^tmprev-[0-9a-f]{32}$")
TOKEN_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_BODY_BYTES = 400_000
MAX_RESULT_CHARS = 300_000
MAX_BUNDLE_BYTES = 900_000
ALLOWED_EVENTS = {
    "probe-loaded",
    "temporary-ui-not-proven",
    "bundle-fetched",
    "bundle-injected",
    "bundle-injection-failed",
    "send-attempted",
    "capture-upload-failed",
    "timeout",
    "stopped",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
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


def validate_event(value: Any, expected_run_id: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {"schema_version", "run_id", "event", "details"}:
        raise ValueError("event payload schema mismatch")
    if value["schema_version"] != 1 or value["run_id"] != expected_run_id:
        raise ValueError("event correlation mismatch")
    if value["event"] not in ALLOWED_EVENTS:
        raise ValueError("unsupported event")
    if type(value["details"]) is not dict:
        raise ValueError("event details must be an object")
    encoded = json.dumps(value["details"], ensure_ascii=False).encode("utf-8")
    if len(encoded) > 32_000:
        raise ValueError("event details too large")
    return dict(value)


def validate_capture(value: Any, expected_run_id: str) -> dict[str, Any]:
    expected = {
        "schema_version",
        "run_id",
        "temporary_state",
        "capture_kind",
        "result_text",
        "diagnostics",
    }
    if type(value) is not dict or set(value) != expected:
        raise ValueError("capture payload schema mismatch")
    if value["schema_version"] != 1 or value["run_id"] != expected_run_id:
        raise ValueError("capture correlation mismatch")
    if value["capture_kind"] not in {"structured", "unstructured"}:
        raise ValueError("invalid capture kind")
    if type(value["result_text"]) is not str or not value["result_text"].strip():
        raise ValueError("result text must be non-empty")
    if len(value["result_text"]) > MAX_RESULT_CHARS:
        raise ValueError("result text too large")
    if type(value["temporary_state"]) is not dict or type(value["diagnostics"]) is not dict:
        raise ValueError("capture diagnostics must be objects")
    return dict(value)


class ProbeState:
    def __init__(self, *, run_id: str, token: str, output_dir: Path, bundle_path: Path | None) -> None:
        self.run_id = run_id
        self.token = token
        self.output_dir = output_dir
        self.bundle_path = bundle_path
        self.progress_path = output_dir / "progress.json"
        self.result_path = output_dir / "result.json"
        self.lock = threading.Lock()
        self.events: list[dict[str, Any]] = []
        self.capture_digest: str | None = None
        self.done = threading.Event()

    def bundle_bytes(self) -> bytes:
        if self.bundle_path is None:
            raise FileNotFoundError("bundle unavailable")
        payload = self.bundle_path.read_bytes()
        if not payload or len(payload) > MAX_BUNDLE_BYTES:
            raise ValueError("invalid bundle size")
        return payload

    def record_event(self, event: dict[str, Any]) -> None:
        with self.lock:
            self.events.append({**event, "received_at": utc_now()})
            self.events = self.events[-200:]
            atomic_json_write(
                self.progress_path,
                {
                    "schema_version": 1,
                    "run_id": self.run_id,
                    "events": self.events,
                    "updated_at": utc_now(),
                },
            )

    def record_capture(self, capture: dict[str, Any]) -> tuple[bool, str]:
        canonical = json.dumps(capture, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()
        with self.lock:
            if self.capture_digest is not None:
                if self.capture_digest == digest:
                    return False, digest
                raise ValueError("different capture already recorded")
            atomic_json_write(
                self.result_path,
                {
                    **capture,
                    "capture_sha256": digest,
                    "received_at": utc_now(),
                },
            )
            self.capture_digest = digest
            self.done.set()
            return True, digest


def make_handler(state: ProbeState):
    class Handler(BaseHTTPRequestHandler):
        server_version = "CAPTemporaryReviewerProbe/0.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _write_json(self, status: int, value: dict[str, Any]) -> None:
            body = json.dumps(value, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/health":
                self._write_json(200, {"schema_version": 1, "status": "ready", "run_id": state.run_id})
                return
            if self.path != "/bundle":
                self._write_json(404, {"status": "not_found"})
                return
            if self.headers.get("X-CAP-Collector-Token") != state.token:
                self._write_json(403, {"status": "forbidden"})
                return
            try:
                payload = state.bundle_bytes()
            except (FileNotFoundError, OSError, ValueError) as exc:
                self._write_json(404, {"status": "bundle_unavailable", "reason": str(exc)[:256]})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self) -> None:
            if self.path not in {"/event", "/capture"}:
                self._write_json(404, {"status": "not_found"})
                return
            if self.headers.get("X-CAP-Collector-Token") != state.token:
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
                if self.path == "/event":
                    event = validate_event(value, state.run_id)
                    state.record_event(event)
                    self._write_json(200, {"status": "recorded"})
                else:
                    capture = validate_capture(value, state.run_id)
                    created, digest = state.record_capture(capture)
                    self._write_json(200, {"status": "recorded" if created else "already_recorded", "sha256": digest})
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                self._write_json(400, {"status": "invalid_payload", "reason": str(exc)[:256]})

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Experiment-only CAP Temporary Reviewer loopback collector")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--bundle-path")
    parser.add_argument("--port", type=int, default=3077)
    parser.add_argument("--timeout-seconds", type=int, default=3000)
    args = parser.parse_args()

    if RUN_ID_RE.fullmatch(args.run_id) is None:
        raise SystemExit("invalid run id")
    if TOKEN_RE.fullmatch(args.token) is None:
        raise SystemExit("invalid token")
    if not 1024 <= args.port <= 65535:
        raise SystemExit("invalid port")
    if not 60 <= args.timeout_seconds <= 7200:
        raise SystemExit("invalid timeout")

    bundle_path = Path(args.bundle_path).resolve() if args.bundle_path else None
    if bundle_path is not None:
        if not bundle_path.is_file() or bundle_path.stat().st_size < 1 or bundle_path.stat().st_size > MAX_BUNDLE_BYTES:
            raise SystemExit("invalid bundle path or size")

    state = ProbeState(
        run_id=args.run_id,
        token=args.token,
        output_dir=Path(args.output_dir).resolve(),
        bundle_path=bundle_path,
    )
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(state))
    server.daemon_threads = True
    worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.25}, daemon=True)
    worker.start()
    print(f"CAP_TEMP_REVIEW_COLLECTOR=ready port={args.port} run_id={args.run_id}", flush=True)
    state.done.wait(args.timeout_seconds)
    server.shutdown()
    server.server_close()
    worker.join(timeout=5)
    return 0 if state.done.is_set() else 3


if __name__ == "__main__":
    raise SystemExit(main())
