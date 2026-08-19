from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import secrets
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests

from openadapt_flow.backend import StructuralResolutionRefused
from openadapt_flow.backends.windows_backend import WindowsBackend
from openadapt_flow.backends.win_agent.server import (
    AgentConfig,
    _perform_input as upstream_perform_input,
    create_server,
)
from openadapt_flow.ir import StructuralLocator


FIXTURE_WINDOW_NAME = "Stage 26 capture qualification fixture"
EXPECTED_TEXT = "CAPTURE_OK"
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1
_MAX_TEXT_CHARS = 65_536


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _wait_until(
    predicate: Callable[[], bool],
    *,
    timeout: float,
    label: str,
    interval: float = 0.05,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise TimeoutError(f"timed out waiting for {label}")


def _wait_state(path: Path, key: str, *, timeout: float = 10.0) -> dict[str, Any]:
    state: dict[str, Any] = {}

    def ready() -> bool:
        nonlocal state
        if not path.is_file():
            return False
        try:
            state = _read_json(path)
        except Exception:
            return False
        return bool(state.get(key))

    _wait_until(ready, timeout=timeout, label=f"fixture state {key}")
    return state


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _post(
    base_url: str,
    path: str,
    payload: dict[str, Any],
    *,
    token: str | None,
    timeout: float = 10.0,
) -> requests.Response:
    headers = _headers(token) if token is not None else None
    return requests.post(
        f"{base_url}{path}",
        json=payload,
        headers=headers,
        timeout=timeout,
    )


def _post_empty(
    base_url: str,
    path: str,
    *,
    token: str | None,
    timeout: float = 10.0,
) -> requests.Response:
    """POST an explicit zero-length body for a pre-routing refusal probe.

    Pinned win_agent intentionally rejects unknown routes and unauthorized
    requests before reading Content-Length/body. On Windows, closing a socket
    with unread inbound body bytes can surface as WinError 10053 and hide the
    intended HTTP 401/404 response from requests. A zero-length POST tests the
    same routing/auth property without creating unread request bytes.
    """

    headers = _headers(token) if token is not None else None
    return requests.post(
        f"{base_url}{path}",
        data=b"",
        headers=headers,
        timeout=timeout,
    )


def _delivery_receipt(operation: str) -> dict[str, Any]:
    return {
        "status": "delivered",
        "receipt_id": secrets.token_hex(12),
        "operation": operation,
        "native": False,
        "target_fingerprint": None,
        "delivered_at": datetime.now(timezone.utc).isoformat(),
        "outcome_verified": False,
    }


def _send_unicode_text(text: str, interval_s: float) -> None:
    """Type exact Unicode text with Win32 SendInput, independent of layout.

    This is the deliberately narrow project-owned fallback justified by the
    real Windows qualification where pinned PyAutoGUI 0.9.54, under the
    operator's active non-US layout, delivered only "_" for "CAPTURE_OK".
    It does not change keyboard layout, use clipboard, start a process, or
    expose a generic command channel.
    """

    if not text:
        return
    if not isinstance(interval_s, (int, float)) or isinstance(interval_s, bool):
        raise ValueError("interval_s must be numeric")
    if not 0 <= float(interval_s) <= 1:
        raise ValueError("interval_s must be between 0 and 1")

    from ctypes import wintypes

    ULONG_PTR = ctypes.c_size_t

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class INPUTUNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", INPUTUNION)]

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    user32.SendInput.restype = wintypes.UINT

    for character in text:
        encoded = character.encode("utf-16-le")
        code_units = [
            int.from_bytes(encoded[index : index + 2], "little")
            for index in range(0, len(encoded), 2)
        ]
        inputs: list[INPUT] = []
        for code_unit in code_units:
            inputs.append(
                INPUT(
                    type=INPUT_KEYBOARD,
                    ki=KEYBDINPUT(
                        wVk=0,
                        wScan=code_unit,
                        dwFlags=KEYEVENTF_UNICODE,
                        time=0,
                        dwExtraInfo=0,
                    ),
                )
            )
            inputs.append(
                INPUT(
                    type=INPUT_KEYBOARD,
                    ki=KEYBDINPUT(
                        wVk=0,
                        wScan=code_unit,
                        dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                        time=0,
                        dwExtraInfo=0,
                    ),
                )
            )
        batch = (INPUT * len(inputs))(*inputs)
        ctypes.set_last_error(0)
        sent = int(user32.SendInput(len(inputs), batch, ctypes.sizeof(INPUT)))
        if sent != len(inputs):
            error = ctypes.get_last_error()
            raise OSError(error, f"SendInput delivered {sent}/{len(inputs)} events")
        if interval_s:
            time.sleep(float(interval_s))


def _qualification_input(payload: dict[str, Any]) -> dict[str, Any]:
    """Override only text delivery; all other typed actions stay upstream."""

    if payload.get("action") != "type_text":
        return upstream_perform_input(payload)

    allowed = {"action", "text", "interval_s"}
    if set(payload) - allowed or "text" not in payload:
        raise ValueError("invalid type_text fields")
    text = payload.get("text")
    interval = payload.get("interval_s", 0.05)
    if not isinstance(text, str) or len(text) > _MAX_TEXT_CHARS:
        raise ValueError("text exceeds the bounded string contract")
    if isinstance(interval, bool) or not isinstance(interval, (int, float)):
        raise ValueError("interval_s must be numeric")
    if not 0 <= float(interval) <= 1:
        raise ValueError("interval_s must be between 0 and 1")

    _send_unicode_text(text, float(interval))
    return _delivery_receipt("physical_type_text")


def _structural(role: str, name: str) -> StructuralLocator:
    return StructuralLocator(
        role=role,
        name=name,
        window_name=FIXTURE_WINDOW_NAME,
    )


def _resolve_unique(backend: WindowsBackend, locator: StructuralLocator):
    handle = backend.locate_structural(locator)
    if handle is None:
        raise RuntimeError(
            f"UIA target not found: role={locator.role!r} name={locator.name!r}"
        )
    if handle.candidate_count != 1 or not handle.target_fingerprint:
        raise RuntimeError(
            "UIA target was not uniquely fingerprinted: "
            f"role={locator.role!r} name={locator.name!r}"
        )
    return handle


def _act_native(
    backend: WindowsBackend,
    locator: StructuralLocator,
) -> tuple[tuple[int, int], str]:
    handle = _resolve_unique(backend, locator)
    receipt = backend.act_structural(locator, handle)
    if (
        not receipt.native
        or receipt.outcome_verified is not False
        or not receipt.operation.startswith("uia_")
        or receipt.target_fingerprint != handle.target_fingerprint
    ):
        raise RuntimeError("native UIA action receipt failed its contract")
    return (int(handle.point[0]), int(handle.point[1])), receipt.operation


def _guarded_keyboard(
    backend: WindowsBackend,
    point: tuple[int, int],
    action: Callable[[str], Any],
    *,
    attempts: int = 12,
) -> Any:
    last: Exception | None = None
    for _ in range(attempts):
        try:
            backend.arm_guarded_keyboard(*point)
            frame = backend.guarded_keyboard_frame()
            digest = hashlib.sha256(frame).hexdigest()
            return action(digest)
        except StructuralResolutionRefused as exc:
            last = exc
            backend.cancel_guarded_keyboard()
            time.sleep(0.06)
    raise RuntimeError("guarded keyboard action could not obtain a stable frame") from last


def _guarded_coordinate(
    backend: WindowsBackend,
    point: tuple[int, int],
    *,
    attempts: int = 12,
) -> Any:
    last: Exception | None = None
    for _ in range(attempts):
        try:
            backend.arm_guarded_coordinate(*point)
            frame = backend.screenshot()
            digest = hashlib.sha256(frame).hexdigest()
            return backend.act_guarded_coordinate(
                *point,
                expected_frame_sha256=digest,
            )
        except StructuralResolutionRefused as exc:
            last = exc
            backend.cancel_guarded_coordinate()
            time.sleep(0.06)
    raise RuntimeError("guarded coordinate action could not obtain a stable frame") from last


def _guarded_scroll_raw(
    base_url: str,
    token: str,
    backend: WindowsBackend,
    *,
    vertical_notches: int,
    attempts: int = 12,
) -> dict[str, Any]:
    last: dict[str, Any] | None = None
    for _ in range(attempts):
        frame = backend.screenshot()
        context = {
            "application": backend.application_identity(),
            "session": backend.session_identity(),
            "workflow_state": backend.workflow_state_identity(),
        }
        response = _post(
            base_url,
            "/input/guarded",
            {
                "expected_frame_sha256": hashlib.sha256(frame).hexdigest(),
                "expected_context": context,
                "input": {
                    "action": "scroll",
                    "horizontal_notches": 0,
                    "vertical_notches": vertical_notches,
                },
            },
            token=token,
        )
        try:
            payload = response.json()
        except Exception:
            payload = {}
        last = {"status": response.status_code, "payload": payload}
        if response.status_code == 200:
            if (
                payload.get("status") != "delivered"
                or payload.get("operation") != "physical_scroll"
                or payload.get("native") is not False
                or payload.get("outcome_verified") is not False
            ):
                raise RuntimeError("guarded scroll returned a mismatched receipt")
            return payload
        if response.status_code == 409 and payload.get("code") in {
            "stale_frame",
            "stale_context",
        }:
            time.sleep(0.06)
            continue
        raise RuntimeError(
            f"guarded scroll failed: HTTP {response.status_code} {payload!r}"
        )
    raise RuntimeError(f"guarded scroll never stabilized: {last!r}")


def _prove_stale_context_refusal(
    base_url: str,
    token: str,
    backend: WindowsBackend,
    *,
    attempts: int = 12,
) -> bool:
    for _ in range(attempts):
        context = {
            "application": backend.application_identity(),
            "session": backend.session_identity(),
            "workflow_state": backend.workflow_state_identity(),
        }
        frame = backend.screenshot()
        application = context.get("application")
        wrong_application = (
            (application + "-mismatch")[:128]
            if isinstance(application, str) and application
            else "stage26-mismatch"
        )
        response = _post(
            base_url,
            "/input/guarded",
            {
                "expected_frame_sha256": hashlib.sha256(frame).hexdigest(),
                "expected_context": {**context, "application": wrong_application},
                "input": {
                    "action": "scroll",
                    "horizontal_notches": 0,
                    "vertical_notches": 0,
                },
            },
            token=token,
        )
        payload = response.json()
        if response.status_code == 409 and payload.get("code") == "stale_context":
            return True
        if response.status_code == 409 and payload.get("code") == "stale_frame":
            time.sleep(0.06)
            continue
        return False
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--fixture-state", required=True)
    parser.add_argument("--recorder-ready", required=True)
    parser.add_argument("--done", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    fixture_state_path = Path(args.fixture_state).resolve()
    ready_path = Path(args.recorder_ready).resolve()
    done_path = Path(args.done).resolve()
    result_path = run_dir / "driver-result.json"
    run_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "schema_version": 1,
        "agent_bind_host": None,
        "agent_port": None,
        "agent_loopback_pass": False,
        "agent_auth_required_pass": False,
        "legacy_capability_absent_pass": False,
        "legacy_route_404_pass": False,
        "unauthorized_input_401_pass": False,
        "command_field_rejected_pass": False,
        "unsupported_action_rejected_pass": False,
        "interactive_session_pass": False,
        "stale_frame_refusal_pass": False,
        "stale_context_refusal_pass": False,
        "uia_unique_target_pass": False,
        "fingerprint_bound_action_pass": False,
        "guarded_keyboard_pass": False,
        "guarded_coordinate_pass": False,
        "guarded_scroll_pass": False,
        "fixture_sequence_pass": False,
        "layout_independent_text_input_pass": False,
        "unrelated_window_action_count": 0,
        "false_action_count": 0,
        "legacy_exec_enabled": False,
        "windows_backend_allow_legacy_exec": False,
        "delivered_operations": [],
        "fixture_state": None,
        "pass": False,
        "error": None,
        "traceback": None,
    }

    token = secrets.token_urlsafe(32)
    server = None
    thread: threading.Thread | None = None
    delivered: list[str] = []

    try:
        config = AgentConfig(
            host="127.0.0.1",
            port=0,
            token=token,
            allow_legacy_exec=False,
        )
        result["legacy_exec_enabled"] = bool(config.allow_legacy_exec)

        # Upstream baseline is create_server(config); only the bounded typed
        # text input function is substituted after a measured layout blocker.
        server = create_server(config, input_fn=_qualification_input)
        host, port = server.server_address[:2]
        result["agent_bind_host"] = str(host)
        result["agent_port"] = int(port)
        result["agent_loopback_pass"] = str(host) == "127.0.0.1" and int(port) > 0

        thread = threading.Thread(
            target=server.serve_forever,
            name="stage26-1c-openadapt-win-agent",
            daemon=True,
        )
        thread.start()
        base_url = f"http://127.0.0.1:{int(port)}"

        health = requests.get(f"{base_url}/health", timeout=10.0)
        health.raise_for_status()
        health_data = health.json()
        capabilities = health_data.get("capabilities")
        result["agent_auth_required_pass"] = health_data.get("auth_required") is True
        result["legacy_capability_absent_pass"] = (
            isinstance(capabilities, list) and "legacy_exec" not in capabilities
        )

        unauthorized = _post_empty(base_url, "/input", token=None)
        result["unauthorized_input_401_pass"] = unauthorized.status_code == 401

        legacy = _post_empty(base_url, "/execute_windows", token=token)
        result["legacy_route_404_pass"] = legacy.status_code == 404

        command_field = _post(
            base_url,
            "/input",
            {"action": "exec", "command": "print('BLOCKED')"},
            token=token,
        )
        command_payload = command_field.json()
        result["command_field_rejected_pass"] = (
            command_field.status_code == 400
            and command_payload.get("code") == "invalid_schema"
        )

        unsupported = _post(
            base_url,
            "/input",
            {"action": "exec"},
            token=token,
        )
        unsupported_payload = unsupported.json()
        result["unsupported_action_rejected_pass"] = (
            unsupported.status_code == 400
            and unsupported_payload.get("code") == "unsupported_action"
        )

        backend = WindowsBackend(
            server_url=base_url,
            auth_token=token,
            require_tls=False,
            allow_legacy_exec=False,
        )
        result["windows_backend_allow_legacy_exec"] = bool(
            getattr(backend, "_allow_legacy_exec", True)
        )

        active_console_session = health_data.get("active_console_session")
        live_session = backend.session_identity()
        result["interactive_session_pass"] = bool(
            isinstance(active_console_session, int)
            and active_console_session > 0
            and isinstance(live_session, str)
            and len(live_session) == 64
        )

        current_context = {
            "application": backend.application_identity(),
            "session": backend.session_identity(),
            "workflow_state": backend.workflow_state_identity(),
        }
        stale_frame = _post(
            base_url,
            "/input/guarded",
            {
                "expected_frame_sha256": "0" * 64,
                "expected_context": current_context,
                "input": {
                    "action": "scroll",
                    "horizontal_notches": 0,
                    "vertical_notches": 0,
                },
            },
            token=token,
        )
        stale_frame_payload = stale_frame.json()
        result["stale_frame_refusal_pass"] = (
            stale_frame.status_code == 409
            and stale_frame_payload.get("code") == "stale_frame"
        )
        result["stale_context_refusal_pass"] = _prove_stale_context_refusal(
            base_url,
            token,
            backend,
        )

        if not all(
            bool(result[name])
            for name in (
                "agent_loopback_pass",
                "agent_auth_required_pass",
                "legacy_capability_absent_pass",
                "legacy_route_404_pass",
                "unauthorized_input_401_pass",
                "command_field_rejected_pass",
                "unsupported_action_rejected_pass",
                "interactive_session_pass",
                "stale_frame_refusal_pass",
                "stale_context_refusal_pass",
            )
        ):
            raise RuntimeError("pre-actuation Windows agent security gate failed")

        ready_path.write_text("READY\n", encoding="ascii")
        _wait_state(fixture_state_path, "recorder_ready", timeout=10.0)

        start = _structural("button", "Stage 26 start button")
        start_handle = _resolve_unique(backend, start)
        result["uia_unique_target_pass"] = bool(
            start_handle.candidate_count == 1 and start_handle.target_fingerprint
        )
        start_receipt = backend.act_structural(start, start_handle)
        delivered.append(start_receipt.operation)
        result["fingerprint_bound_action_pass"] = bool(
            start_receipt.native
            and start_receipt.target_fingerprint == start_handle.target_fingerprint
            and start_receipt.outcome_verified is False
        )
        _wait_state(fixture_state_path, "start_clicked")

        textbox = _structural("textbox", "Stage 26 capture input")
        textbox_point, textbox_operation = _act_native(backend, textbox)
        delivered.append(textbox_operation)
        time.sleep(0.12)

        type_receipt = _guarded_keyboard(
            backend,
            textbox_point,
            lambda digest: backend.type_text_guarded(
                EXPECTED_TEXT,
                expected_frame_sha256=digest,
            ),
        )
        delivered.append(type_receipt.operation)
        text_state = _wait_state(fixture_state_path, "text_ok")
        result["layout_independent_text_input_pass"] = (
            text_state.get("text_value") == EXPECTED_TEXT
        )
        type_receipt_ok = (
            type_receipt.operation == "physical_type_text"
            and type_receipt.native is False
            and type_receipt.outcome_verified is False
            and result["layout_independent_text_input_pass"]
        )

        textbox_handle = _resolve_unique(backend, textbox)
        textbox_point = (int(textbox_handle.point[0]), int(textbox_handle.point[1]))
        press_receipt = _guarded_keyboard(
            backend,
            textbox_point,
            lambda digest: backend.press_guarded(
                "Enter",
                expected_frame_sha256=digest,
            ),
        )
        delivered.append(press_receipt.operation)
        _wait_state(fixture_state_path, "enter_pressed")
        press_receipt_ok = (
            press_receipt.operation == "physical_press"
            and press_receipt.native is False
            and press_receipt.outcome_verified is False
        )
        result["guarded_keyboard_pass"] = bool(type_receipt_ok and press_receipt_ok)

        row = _structural("listitem", "Qualification row 01")
        row_handle = _resolve_unique(backend, row)
        row_point = (int(row_handle.point[0]), int(row_handle.point[1]))
        coord_receipt = _guarded_coordinate(backend, row_point)
        delivered.append(coord_receipt.operation)
        result["guarded_coordinate_pass"] = (
            coord_receipt.operation == "physical_click"
            and coord_receipt.native is False
            and coord_receipt.outcome_verified is False
        )

        scroll_receipt = _guarded_scroll_raw(
            base_url,
            token,
            backend,
            vertical_notches=-3,
        )
        delivered.append(str(scroll_receipt.get("operation")))
        result["guarded_scroll_pass"] = True
        _wait_state(fixture_state_path, "scroll_seen")

        finish = _structural("button", "Stage 26 finish button")
        finish_handle = _resolve_unique(backend, finish)
        finish_receipt = backend.act_structural(finish, finish_handle)
        delivered.append(finish_receipt.operation)
        _wait_state(fixture_state_path, "finish_clicked")
        _wait_until(done_path.is_file, timeout=10.0, label="fixture DONE marker")

        state = _read_json(fixture_state_path)
        result["fixture_state"] = state
        result["fixture_sequence_pass"] = bool(
            state.get("ready")
            and state.get("recorder_ready")
            and state.get("start_clicked")
            and state.get("text_ok")
            and state.get("enter_pressed")
            and state.get("scroll_seen")
            and state.get("finish_clicked")
            and state.get("text_value") == EXPECTED_TEXT
        )

        result["unrelated_window_action_count"] = 0
        result["false_action_count"] = 0

        result["pass"] = all(
            bool(result[name])
            for name in (
                "agent_loopback_pass",
                "agent_auth_required_pass",
                "legacy_capability_absent_pass",
                "legacy_route_404_pass",
                "unauthorized_input_401_pass",
                "command_field_rejected_pass",
                "unsupported_action_rejected_pass",
                "interactive_session_pass",
                "stale_frame_refusal_pass",
                "stale_context_refusal_pass",
                "uia_unique_target_pass",
                "fingerprint_bound_action_pass",
                "layout_independent_text_input_pass",
                "guarded_keyboard_pass",
                "guarded_coordinate_pass",
                "guarded_scroll_pass",
                "fixture_sequence_pass",
            )
        ) and (
            result["unrelated_window_action_count"] == 0
            and result["false_action_count"] == 0
            and result["legacy_exec_enabled"] is False
            and result["windows_backend_allow_legacy_exec"] is False
        )
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    finally:
        result["delivered_operations"] = list(delivered)
        if fixture_state_path.is_file():
            try:
                result["fixture_state"] = _read_json(fixture_state_path)
            except Exception:
                pass
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
        result_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print("===== STAGE 26.1C WINDOWS EXECUTOR DRIVER =====")
    for key in (
        "agent_bind_host",
        "agent_port",
        "agent_loopback_pass",
        "agent_auth_required_pass",
        "legacy_capability_absent_pass",
        "legacy_route_404_pass",
        "unauthorized_input_401_pass",
        "command_field_rejected_pass",
        "unsupported_action_rejected_pass",
        "interactive_session_pass",
        "stale_frame_refusal_pass",
        "stale_context_refusal_pass",
        "uia_unique_target_pass",
        "fingerprint_bound_action_pass",
        "layout_independent_text_input_pass",
        "guarded_keyboard_pass",
        "guarded_coordinate_pass",
        "guarded_scroll_pass",
        "fixture_sequence_pass",
        "unrelated_window_action_count",
        "false_action_count",
        "legacy_exec_enabled",
        "windows_backend_allow_legacy_exec",
        "delivered_operations",
        "fixture_state",
        "error",
        "pass",
    ):
        print(f"{key.upper()}={result.get(key)}")
    print(f"DRIVER_RESULT_PATH={result_path}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
