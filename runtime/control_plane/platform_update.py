from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
from typing import Any


PROCEDURE_ID = "platform_update_v1"
_MAX_JSON_BYTES = 64 * 1024
_CHECK_TIMEOUT_SECONDS = 120
_UPDATE_CHILD_FLAG = "--run-installed-updater"
_REQUEST_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_REQUEST_HISTORY_LIMIT = 128
_REQUEST_RECONCILIATION_DEADLINE_SECONDS = 60 * 60


def _local_root(local_app_data: Path | None = None) -> Path:
    if local_app_data is None:
        raw = os.environ.get("LOCALAPPDATA")
        if not raw:
            raise RuntimeError("LOCALAPPDATA is required for platform update")
        local_app_data = Path(raw)
    return Path(local_app_data) / "ChatAgentPlatform"


def _paths(local_app_data: Path | None = None) -> dict[str, Path]:
    root = _local_root(local_app_data)
    state = root / "state"
    return {
        "root": root,
        "updater": root / "app" / "scripts" / "chat-platform-update.ps1",
        "state": state / "platform-update.json",
        "result": state / "platform-update-result.json",
        "requests": state / "platform-update-requests",
    }


def _require_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("platform update procedure is available only on Windows")


def _pwsh() -> str:
    executable = shutil.which("pwsh.exe") or shutil.which("pwsh")
    if not executable:
        raise RuntimeError("PowerShell 7 (pwsh.exe) is required")
    return str(Path(executable).resolve())


def _python() -> str:
    executable = Path(sys.executable)
    if not executable.is_absolute():
        raise RuntimeError("platform update Python interpreter path is not absolute")
    return str(executable.resolve())


def _require_updater(path: Path) -> Path:
    if not path.is_file():
        raise RuntimeError("installed platform updater is missing")
    return path.resolve()


def _read_bounded_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if not path.is_file():
        raise RuntimeError(f"platform update state is not a regular file: {path.name}")
    size = path.stat().st_size
    if size > _MAX_JSON_BYTES:
        raise RuntimeError(f"platform update state exceeds {_MAX_JSON_BYTES} bytes: {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"platform update state is invalid JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"platform update state must be a JSON object: {path.name}")
    return value


def _write_atomic_json(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    if len(payload.encode("utf-8")) > _MAX_JSON_BYTES:
        raise RuntimeError("platform update request record exceeds bounded JSON limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _parse_updater_stdout(stdout: str) -> dict[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("platform updater returned no JSON result")
    try:
        value = json.loads(lines[-1])
    except Exception as exc:
        raise RuntimeError("platform updater returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("platform updater result must be a JSON object")
    return value


def _fixed_argv(updater: Path, action: str, request_id: str | None = None) -> list[str]:
    argv = [
        _pwsh(),
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(updater),
        "-Action",
        action,
    ]
    if request_id is not None:
        if action != "Update":
            raise RuntimeError("request_id is valid only for update execution")
        argv.extend(["-RequestId", _validate_request_id(request_id)])
    return argv


def _validate_request_id(request_id: object) -> str:
    if not isinstance(request_id, str) or _REQUEST_ID_RE.fullmatch(request_id) is None:
        raise ValueError("request_id must be a 32-character lowercase hex string")
    return request_id


def _request_path(paths: dict[str, Path], request_id: str) -> Path:
    return paths["requests"] / f"{request_id}.request.json"


def _receipt_path(paths: dict[str, Path], request_id: str) -> Path:
    return paths["requests"] / f"{request_id}.receipt.json"


def _updater_result_path(paths: dict[str, Path], request_id: str) -> Path:
    return paths["requests"] / f"{request_id}.updater.json"


def _accepted_at(record: dict[str, Any]) -> datetime:
    raw = record.get("accepted_at")
    if not isinstance(raw, str):
        raise RuntimeError("platform update request accepted_at is missing")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError("platform update request accepted_at is invalid") from exc
    if parsed.tzinfo is None:
        raise RuntimeError("platform update request accepted_at must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _completed_at(result: dict[str, Any]) -> datetime:
    raw = result.get("completed_at")
    if not isinstance(raw, str):
        raise RuntimeError("platform updater completed_at is missing")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError("platform updater completed_at is invalid") from exc
    if parsed.tzinfo is None:
        raise RuntimeError("platform updater completed_at must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _check(paths: dict[str, Path]) -> dict[str, Any]:
    updater = _require_updater(paths["updater"])
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    completed = subprocess.run(
        _fixed_argv(updater, "Check"),
        cwd=str(updater.parent),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_CHECK_TIMEOUT_SECONDS,
        shell=False,
        creationflags=creationflags,
        check=False,
    )
    result = _parse_updater_stdout(completed.stdout)
    if completed.returncode not in {0, 3, 4} and result.get("status") != "error":
        raise RuntimeError(f"platform updater check failed with exit code {completed.returncode}")
    return {
        "schema_version": 1,
        "status": "completed",
        "action": "check",
        "updater": result,
    }


def _trampoline_argv(request_id: str) -> list[str]:
    return [_python(), str(Path(__file__).resolve()), _UPDATE_CHILD_FLAG, request_id]


def _write_child_error(
    paths: dict[str, Path],
    request_id: str,
    *,
    reason: str,
    updater_process_id: int | None = None,
    updater_exit_code: int | None = None,
) -> None:
    _write_atomic_json(
        _receipt_path(paths, request_id),
        {
            "schema_version": 1,
            "request_id": request_id,
            "status": "error",
            "correlation_verified": False,
            "reason": reason,
            "updater_process_id": updater_process_id,
            "updater_exit_code": updater_exit_code,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def _correlated_updater_result(
    *,
    request_id: str,
    accepted: datetime,
    result: dict[str, Any] | None,
    updater_pid: int | None = None,
) -> bool:
    if result is None:
        return False
    if (
        result.get("request_id") != request_id
        or result.get("action") != "update"
        or type(result.get("process_id")) is not int
        or _completed_at(result) < accepted
    ):
        return False
    if updater_pid is not None and result["process_id"] != updater_pid:
        return False
    return True


def _receipt_from_updater_result(
    *,
    request_id: str,
    result: dict[str, Any],
    updater_exit_code: int | None,
    recovered_by_status: bool,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "request_id": request_id,
        "status": "completed",
        "correlation_verified": True,
        "updater_process_id": int(result["process_id"]),
        "updater_exit_code": updater_exit_code,
        "updater_result": result,
        "recovered_by_status": recovered_by_status,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def _run_installed_updater_child(
    request_id: str,
    *,
    local_app_data: Path | None = None,
) -> int:
    _require_windows()
    request_id = _validate_request_id(request_id)
    paths = _paths(local_app_data)
    request = _read_bounded_json(_request_path(paths, request_id))
    if request is None or request.get("request_id") != request_id:
        return 65
    try:
        accepted = _accepted_at(request)
        updater = _require_updater(paths["updater"])
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        process = subprocess.Popen(
            _fixed_argv(updater, "Update", request_id),
            cwd=str(updater.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            close_fds=True,
            creationflags=creationflags,
        )
    except Exception:
        _write_child_error(paths, request_id, reason="updater_launch_failed")
        return 1

    updater_pid = int(process.pid)
    try:
        exit_code = int(process.wait())
    except Exception:
        _write_child_error(
            paths,
            request_id,
            reason="updater_wait_failed",
            updater_process_id=updater_pid,
        )
        return 1

    try:
        result = _read_bounded_json(_updater_result_path(paths, request_id))
        correlated = _correlated_updater_result(
            request_id=request_id,
            accepted=accepted,
            result=result,
            updater_pid=updater_pid,
        )
    except Exception:
        correlated = False
        result = None

    if not correlated or result is None:
        _write_child_error(
            paths,
            request_id,
            reason="updater_result_not_correlated",
            updater_process_id=updater_pid,
            updater_exit_code=exit_code,
        )
        return 2

    _write_atomic_json(
        _receipt_path(paths, request_id),
        _receipt_from_updater_result(
            request_id=request_id,
            result=result,
            updater_exit_code=exit_code,
            recovered_by_status=False,
        ),
    )
    return 0


def _request_update(paths: dict[str, Path]) -> dict[str, Any]:
    _require_updater(paths["updater"])
    requests_dir = paths["requests"]
    requests_dir.mkdir(parents=True, exist_ok=True)
    if len(list(requests_dir.glob("*.request.json"))) >= _REQUEST_HISTORY_LIMIT:
        raise RuntimeError("platform update request history limit reached")

    request_id = secrets.token_hex(16)
    accepted_at = datetime.now(timezone.utc).isoformat()
    request_path = _request_path(paths, request_id)
    _write_atomic_json(
        request_path,
        {
            "schema_version": 1,
            "request_id": request_id,
            "status": "accepted",
            "accepted_at": accepted_at,
            "repository": "BogdanAIP/chat-agent-platform",
            "branch": "main",
        },
    )

    creationflags = (
        getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        | getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
    )
    try:
        process = subprocess.Popen(
            _trampoline_argv(request_id),
            cwd=str(Path(__file__).resolve().parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            close_fds=True,
            creationflags=creationflags,
        )
    except Exception:
        try:
            request_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    return {
        "schema_version": 1,
        "status": "accepted",
        "action": "request_update",
        "request_id": request_id,
        "process_id": int(process.pid),
        "outcome_verified": False,
        "reconcile_with": {
            "procedure": PROCEDURE_ID,
            "action": "status",
            "request_id": request_id,
        },
    }


def _status(paths: dict[str, Path], request_id: str) -> dict[str, Any]:
    request_id = _validate_request_id(request_id)
    request = _read_bounded_json(_request_path(paths, request_id))
    if request is None or request.get("request_id") != request_id:
        raise ValueError("unknown platform update request_id")
    accepted = _accepted_at(request)
    receipt = _read_bounded_json(_receipt_path(paths, request_id))

    if receipt is None:
        updater_result = _read_bounded_json(_updater_result_path(paths, request_id))
        if _correlated_updater_result(
            request_id=request_id,
            accepted=accepted,
            result=updater_result,
        ):
            assert updater_result is not None
            receipt = _receipt_from_updater_result(
                request_id=request_id,
                result=updater_result,
                updater_exit_code=None,
                recovered_by_status=True,
            )
            _write_atomic_json(_receipt_path(paths, request_id), receipt)

    if receipt is None:
        age_seconds = (datetime.now(timezone.utc) - accepted).total_seconds()
        if age_seconds >= _REQUEST_RECONCILIATION_DEADLINE_SECONDS:
            return {
                "schema_version": 1,
                "status": "manual_recovery_required",
                "action": "status",
                "request_id": request_id,
                "reason": "request_specific_updater_result_unavailable",
                "request": request,
                "receipt": None,
            }

    return {
        "schema_version": 1,
        "status": "pending" if receipt is None else "completed",
        "action": "status",
        "request_id": request_id,
        "request": request,
        "receipt": receipt,
    }


def run_platform_update(
    request: dict[str, Any],
    *,
    local_app_data: Path | None = None,
) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    if request.get("procedure") != PROCEDURE_ID:
        raise ValueError("unexpected procedure id")
    action = request.get("action")
    if action not in {"check", "request_update", "status"}:
        raise ValueError("unsupported platform update action")

    expected_keys = (
        {"procedure", "action", "request_id"}
        if action == "status"
        else {"procedure", "action"}
    )
    if set(request) != expected_keys:
        if action == "status":
            raise ValueError("platform update status accepts only procedure, action and request_id")
        raise ValueError("platform update request accepts only procedure and action")

    _require_windows()
    paths = _paths(local_app_data)
    if action == "check":
        return _check(paths)
    if action == "request_update":
        return _request_update(paths)
    return _status(paths, request["request_id"])


if __name__ == "__main__":
    if (
        len(sys.argv) != 3
        or sys.argv[1] != _UPDATE_CHILD_FLAG
        or _REQUEST_ID_RE.fullmatch(sys.argv[2]) is None
    ):
        raise SystemExit(64)
    raise SystemExit(_run_installed_updater_child(sys.argv[2]))
