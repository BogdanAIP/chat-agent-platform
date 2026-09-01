from __future__ import annotations

import json
import os
import re
import struct
import sys
from pathlib import Path
from typing import Any, BinaryIO, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.control_plane.independent_review_dispatch import (  # noqa: E402
    cleanup_review_evidence,
    dispatch_install_state_root,
    get_review_dispatch_chunk,
)
from runtime.control_plane.independent_review_state import (  # noqa: E402
    MAX_RESULT_BYTES,
    ReviewStateError,
    submit_independent_review_result,
)


HOST_NAME = "com.chat_agent_platform.reviewer"
EXTENSION_ID = "fglkcklejbabngidbncknblmningkkhl"
EXPECTED_ORIGIN = f"chrome-extension://{EXTENSION_ID}/"
SCHEMA_VERSION = 1
GET_DISPATCH = "get_review_dispatch_v1"
SUBMIT_RESULT = "submit_review_result_v1"
MAX_REQUEST_BYTES = MAX_RESULT_BYTES * 6 + 65_536
MAX_RESPONSE_BYTES = 900_000
_REVIEW_RUN_ID_RE = re.compile(r"^[0-9a-f]{64}$")


class NativeHostError(ValueError):
    pass


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise NativeHostError(
            f"{label} keys mismatch: missing={sorted(expected - actual) or 'none'} "
            f"unexpected={sorted(actual - expected) or 'none'}"
        )


def _review_run_id(value: Any) -> str:
    if type(value) is not str or _REVIEW_RUN_ID_RE.fullmatch(value) is None:
        raise NativeHostError("review_run_id must be a 64-character lowercase hex capability")
    return value


def _dispatch_request(value: Mapping[str, Any], *, state_root: Path) -> dict[str, Any]:
    _require_exact_keys(
        value,
        {"schema_version", "type", "review_run_id", "cursor"},
        "get_review_dispatch_v1",
    )
    if value["schema_version"] != SCHEMA_VERSION or value["type"] != GET_DISPATCH:
        raise NativeHostError("get_review_dispatch_v1 envelope mismatch")
    run_id = _review_run_id(value["review_run_id"])
    cursor = value["cursor"]
    if type(cursor) is not int:
        raise NativeHostError("dispatch cursor must be an integer")
    return get_review_dispatch_chunk(
        review_run_id=run_id,
        cursor=cursor,
        state_root=state_root,
    )


def _submit_request(value: Mapping[str, Any], *, state_root: Path) -> dict[str, Any]:
    _require_exact_keys(
        value,
        {"schema_version", "type", "review_run_id", "result"},
        "submit_review_result_v1",
    )
    if value["schema_version"] != SCHEMA_VERSION or value["type"] != SUBMIT_RESULT:
        raise NativeHostError("submit_review_result_v1 envelope mismatch")
    run_id = _review_run_id(value["review_run_id"])
    result = value["result"]
    if type(result) is not str or not result.strip():
        raise NativeHostError("review result must be non-empty text")
    if len(result.encode("utf-8")) > MAX_RESULT_BYTES:
        raise NativeHostError("review result exceeds the accepted bound")

    dispatch = get_review_dispatch_chunk(
        review_run_id=run_id,
        cursor=0,
        state_root=state_root,
    )
    completion = dispatch.get("completion_marker")
    if type(completion) is not str or not result.rstrip().endswith(completion):
        raise NativeHostError("review result does not end with the exact dispatch completion marker")

    recorded = submit_independent_review_result(
        {"review_run_id": run_id, "result": result},
        state_root=state_root,
    )
    cleanup_ok = True
    try:
        cleanup_ok = cleanup_review_evidence(review_run_id=run_id, state_root=state_root)
    except (OSError, ReviewStateError):
        cleanup_ok = False
    return {
        "schema_version": 1,
        "type": "submit_review_result_receipt_v1",
        "review_run_id": run_id,
        "status": recorded["status"],
        "operation_key": recorded["operation_key"],
        "result_body_sha256": recorded["result_body_sha256"],
        "evidence_cleanup_ok": cleanup_ok,
    }


def handle_message(value: Mapping[str, Any], *, state_root: Path) -> dict[str, Any]:
    if type(value) is not dict:
        raise NativeHostError("native message must be a plain object")
    message_type = value.get("type")
    if message_type == GET_DISPATCH:
        return _dispatch_request(value, state_root=state_root)
    if message_type == SUBMIT_RESULT:
        return _submit_request(value, state_root=state_root)
    raise NativeHostError("unsupported reviewer native message type")


def _read_exact(stream: BinaryIO, count: int) -> bytes:
    chunks: list[bytes] = []
    remaining = count
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise EOFError
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_native_message(stream: BinaryIO) -> dict[str, Any] | None:
    prefix = stream.read(4)
    if prefix == b"":
        return None
    if len(prefix) != 4:
        raise NativeHostError("native message length prefix is truncated")
    (length,) = struct.unpack("<I", prefix)
    if length < 2 or length > MAX_REQUEST_BYTES:
        raise NativeHostError("native request length exceeds the accepted bound")
    try:
        raw = _read_exact(stream, length)
    except EOFError as exc:
        raise NativeHostError("native message body is truncated") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise NativeHostError("native message is not valid UTF-8 JSON") from exc
    if type(value) is not dict:
        raise NativeHostError("native message must decode to an object")
    return value


def write_native_message(stream: BinaryIO, value: Mapping[str, Any]) -> None:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if not payload or len(payload) > MAX_RESPONSE_BYTES:
        raise NativeHostError("native response exceeds the Chrome host-to-extension bound")
    stream.write(struct.pack("<I", len(payload)))
    stream.write(payload)
    stream.flush()


def _error_response(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, (NativeHostError, ReviewStateError)):
        reason = str(exc)
    else:
        reason = f"runtime_unavailable:{type(exc).__name__}"
    return {
        "schema_version": 1,
        "type": "reviewer_native_error_v1",
        "status": "error",
        "reason": reason[:512],
    }


def _require_chrome_origin(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != EXPECTED_ORIGIN:
        raise NativeHostError("native host caller origin is not the installed reviewer extension")


def main() -> int:
    try:
        _require_chrome_origin(sys.argv)
        state_root = dispatch_install_state_root()
        if os.name == "nt":
            import msvcrt

            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    except Exception as exc:
        try:
            write_native_message(sys.stdout.buffer, _error_response(exc))
        except Exception:
            pass
        return 2

    while True:
        try:
            request = read_native_message(sys.stdin.buffer)
            if request is None:
                return 0
            response = handle_message(request, state_root=state_root)
        except Exception as exc:
            response = _error_response(exc)
        try:
            write_native_message(sys.stdout.buffer, response)
        except Exception:
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
