from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import secrets
import shutil
import subprocess
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Callable

import requests

from openadapt_flow.backends.windows_backend import WindowsBackend
from openadapt_flow.backends.win_agent.server import AgentConfig, create_server

from runtime.windows.actuation import bounded_input
from runtime.windows.native_point_guard import NativePointGuardError, require_foreground_hit_target
from runtime.windows.observation import ControlObservation, DesktopState, observe_bound_window
from runtime.windows.verifier import VerificationStatus, verify_expected_fields
from runtime.windows.window_scoped_uia import WindowScopedUiaResolver


WM_CLOSE = 0x0010
EXPECTED_EXECUTABLE = "code.exe"
FOCUSED_EDITOR_ROLES = {"textbox", "document", "pane", "custom", "group", "edit"}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _artifact_evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "size": None, "sha256": None}
    data = _read_bytes(path)
    return {"exists": True, "size": len(data), "sha256": _sha256_bytes(data)}


def _workspace_snapshot(root: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    if not root.is_dir():
        return rows
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows[path.relative_to(root).as_posix()] = _sha256_bytes(path.read_bytes())
    return rows


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


def _enum_visible_windows() -> list[dict[str, Any]]:
    if not hasattr(ctypes, "WinDLL"):
        raise RuntimeError("real application qualification requires Windows")

    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    windows: list[dict[str, Any]] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = int(user32.GetWindowTextLengthW(hwnd))
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if not title:
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) > 0:
            windows.append({"hwnd": int(hwnd), "pid": int(pid.value), "title": title})
        return True

    callback_fn = callback_type(callback)
    if not user32.EnumWindows(callback_fn, 0):
        error = ctypes.get_last_error()
        raise OSError(error, "EnumWindows failed")
    return windows


def _matching_vscode_windows(unique_filename: str) -> list[dict[str, Any]]:
    needle = unique_filename.casefold()
    return [row for row in _enum_visible_windows() if needle in str(row["title"]).casefold()]


def _wait_unique_vscode_window(unique_filename: str, timeout: float) -> dict[str, Any]:
    selected: dict[str, Any] | None = None

    def ready() -> bool:
        nonlocal selected
        matches = _matching_vscode_windows(unique_filename)
        if len(matches) != 1:
            return False
        selected = matches[0]
        return True

    _wait_until(ready, timeout=timeout, label="one isolated VS Code window")
    assert selected is not None
    return selected


def _post_close(hwnd: int) -> None:
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    if not user32.PostMessageW(hwnd, WM_CLOSE, 0, 0):
        error = ctypes.get_last_error()
        raise OSError(error, "PostMessageW(WM_CLOSE) failed")


def _same_window_identity(before: DesktopState, after: DesktopState) -> bool:
    return (
        before.session_id == after.session_id
        and before.application_identity == after.application_identity
        and before.executable_name.casefold() == after.executable_name.casefold()
        and before.process_id == after.process_id
        and before.process_generation == after.process_generation
        and before.window_handle == after.window_handle
        and before.window_instance == after.window_instance
        and before.window_title == after.window_title
    )


def _focused_editor_control(state: DesktopState, unique_filename: str) -> ControlObservation | None:
    if not state.focused_control:
        return None
    matches = [
        control
        for control in state.controls
        if control.observation_fingerprint == state.focused_control
    ]
    if len(matches) != 1:
        return None
    control = matches[0]
    if control.bounds is None or control.bounds.width <= 0 or control.bounds.height <= 0:
        return None
    if control.visible is not True or control.enabled is not True or control.focused is not True:
        return None
    role = control.role.casefold()
    if role not in FOCUSED_EDITOR_ROLES:
        return None
    name = control.name.casefold()
    filename = unique_filename.casefold()
    if role != "textbox" and filename not in name and "text editor" not in name:
        return None
    return control


def _control_center(control: ControlObservation) -> tuple[int, int]:
    if control.bounds is None:
        raise RuntimeError("focused editor control has no bounds")
    return (
        int(round((control.bounds.left + control.bounds.right) / 2.0)),
        int(round((control.bounds.top + control.bounds.bottom) / 2.0)),
    )


def _verification_decision(status: VerificationStatus) -> str:
    return "continue" if status is VerificationStatus.PASS else "abstain"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--app-root", required=True)
    parser.add_argument("--code-exe", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    app_root = Path(args.app_root).resolve()
    code_exe = Path(args.code_exe).resolve()
    timeout = float(args.timeout_seconds)
    result_path = run_dir / "vscode-real-app-result.json"
    run_dir.mkdir(parents=True, exist_ok=True)

    workspace_root = app_root / "workspace"
    user_data_root = app_root / "user-data"
    extensions_root = app_root / "extensions"
    user_settings_dir = user_data_root / "User"
    unique_filename = f"chat-agent-stage26e-{secrets.token_hex(6)}.txt"
    target_file = workspace_root / unique_filename
    marker = f"CHAT_AGENT_STAGE26E_OK_{secrets.token_hex(8)}"
    marker_bytes = marker.encode("utf-8")

    result: dict[str, Any] = {
        "schema_version": 1,
        "qualification_kind": "real-application-vscode-disposable-text-edit",
        "code_exe": str(code_exe),
        "application_discovery_pass": False,
        "isolated_profile_pass": False,
        "disposable_workspace_pass": False,
        "preexisting_target_window_count": None,
        "window_title": None,
        "window_process_id": None,
        "window_binding_pass": False,
        "desktop_observation_pass": False,
        "focused_editor_precondition_pass": False,
        "focused_editor_role": None,
        "focused_editor_name": None,
        "native_point_guard_pass": False,
        "agent_loopback_pass": False,
        "agent_auth_required_pass": False,
        "legacy_capability_absent_pass": False,
        "baseline_artifact_evidence": None,
        "baseline_verification_status": None,
        "mismatch_probe_verification_status": None,
        "mismatch_probe_decision": None,
        "mismatch_probe_zero_action_pass": False,
        "guarded_keyboard_delivery_pass": False,
        "keyboard_action_count": 0,
        "current_state_verification_pass": False,
        "completion_verification_status": None,
        "completion_verification_pass": False,
        "workspace_expected_only_pass": False,
        "workspace_snapshot": None,
        "rollback_pass": False,
        "application_cleanup_pass": False,
        "app_root_cleanup_pass": False,
        "resolver_stats": None,
        "pass": False,
        "error": None,
        "traceback": None,
    }

    resolver = WindowScopedUiaResolver()
    server = None
    server_thread: threading.Thread | None = None
    cli_process: subprocess.Popen[bytes] | None = None
    bound_hwnd: int | None = None

    try:
        result["application_discovery_pass"] = bool(
            code_exe.is_file() and code_exe.name.casefold() == EXPECTED_EXECUTABLE
        )
        if not result["application_discovery_pass"]:
            raise RuntimeError("VS Code executable was not resolved to Code.exe")

        if app_root.exists():
            shutil.rmtree(app_root)
        workspace_root.mkdir(parents=True, exist_ok=False)
        user_settings_dir.mkdir(parents=True, exist_ok=False)
        extensions_root.mkdir(parents=True, exist_ok=False)
        target_file.write_bytes(b"")
        settings = {
            "files.autoSave": "afterDelay",
            "files.autoSaveDelay": 100,
            "workbench.startupEditor": "none",
            "window.restoreWindows": "none",
            "security.workspace.trust.enabled": False,
            "extensions.autoCheckUpdates": False,
            "extensions.autoUpdate": False,
            "update.mode": "none",
        }
        (user_settings_dir / "settings.json").write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        result["isolated_profile_pass"] = user_data_root.is_dir() and extensions_root.is_dir()
        result["disposable_workspace_pass"] = (
            workspace_root.is_dir() and target_file.is_file() and app_root.parent == Path(args.app_root).resolve().parent
        )

        baseline = _artifact_evidence(target_file)
        result["baseline_artifact_evidence"] = baseline
        baseline_verify = verify_expected_fields(
            before={},
            after=baseline,
            expectation={"exists": True, "size": 0, "sha256": _sha256_bytes(b"")},
        )
        result["baseline_verification_status"] = baseline_verify.status.value
        if not baseline_verify.passed:
            raise RuntimeError("disposable baseline artifact verification failed")

        preexisting = _matching_vscode_windows(unique_filename)
        result["preexisting_target_window_count"] = len(preexisting)
        if preexisting:
            raise RuntimeError("unique VS Code qualification title already exists")

        cli_process = subprocess.Popen(
            [
                str(code_exe),
                "--wait",
                "--new-window",
                "--disable-extensions",
                "--user-data-dir",
                str(user_data_root),
                "--extensions-dir",
                str(extensions_root),
                "--goto",
                f"{target_file}:1:1",
            ],
            cwd=str(workspace_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )

        window = _wait_unique_vscode_window(unique_filename, timeout)
        bound_hwnd = int(window["hwnd"])
        window_pid = int(window["pid"])
        window_title = str(window["title"])
        result["window_title"] = window_title
        result["window_process_id"] = window_pid
        resolver.set_expected_process_id(window_pid)

        before_state = observe_bound_window(resolver, window_title)
        result["window_binding_pass"] = bool(
            before_state.window_handle == bound_hwnd
            and before_state.process_id == window_pid
            and before_state.executable_name.casefold() == EXPECTED_EXECUTABLE
        )
        result["desktop_observation_pass"] = bool(
            before_state.controls
            and before_state.window_bounds.width > 0
            and before_state.window_bounds.height > 0
            and before_state.window_instance
        )
        if not result["window_binding_pass"] or not result["desktop_observation_pass"]:
            raise RuntimeError("VS Code DesktopState binding/observation failed")

        focused = _focused_editor_control(before_state, unique_filename)
        if focused is None:
            focused_rows = [
                {
                    "role": item.role,
                    "name": item.name,
                    "visible": item.visible,
                    "enabled": item.enabled,
                    "focused": item.focused,
                }
                for item in before_state.controls
                if item.focused is True
            ]
            result["focused_control_diagnostics"] = focused_rows[:8]
            raise RuntimeError("VS Code editor did not expose one safe focused editor control")
        result["focused_editor_precondition_pass"] = True
        result["focused_editor_role"] = focused.role
        result["focused_editor_name"] = focused.name
        focus_point = _control_center(focused)
        require_foreground_hit_target(before_state, *focus_point)
        result["native_point_guard_pass"] = True

        token = secrets.token_urlsafe(32)
        server = create_server(
            AgentConfig(host="127.0.0.1", port=0, token=token, allow_legacy_exec=False),
            input_fn=bounded_input,
            uia_fn=resolver.perform,
        )
        host, port = server.server_address[:2]
        result["agent_loopback_pass"] = str(host) == "127.0.0.1" and int(port) > 0
        server_thread = threading.Thread(
            target=server.serve_forever,
            name="stage26-2e-vscode-win-agent",
            daemon=True,
        )
        server_thread.start()
        base_url = f"http://127.0.0.1:{int(port)}"
        health = requests.get(f"{base_url}/health", timeout=10.0)
        health.raise_for_status()
        health_data = health.json()
        result["agent_auth_required_pass"] = health_data.get("auth_required") is True
        result["legacy_capability_absent_pass"] = "legacy_exec" not in (health_data.get("capabilities") or [])
        if not all(
            bool(result[name])
            for name in (
                "agent_loopback_pass",
                "agent_auth_required_pass",
                "legacy_capability_absent_pass",
            )
        ):
            raise RuntimeError("real-app Windows agent security precondition failed")

        backend = WindowsBackend(
            server_url=base_url,
            auth_token=token,
            require_tls=False,
            allow_legacy_exec=False,
        )

        mismatch = verify_expected_fields(
            before={},
            after=baseline,
            expectation={"exists": True, "size": 0, "sha256": "0" * 64},
        )
        result["mismatch_probe_verification_status"] = mismatch.status.value
        result["mismatch_probe_decision"] = _verification_decision(mismatch.status)
        result["mismatch_probe_zero_action_pass"] = bool(
            result["mismatch_probe_decision"] == "abstain" and result["keyboard_action_count"] == 0
        )
        if not result["mismatch_probe_zero_action_pass"]:
            raise RuntimeError("recoverable mismatch probe did not fail closed before mutation")

        require_foreground_hit_target(before_state, *focus_point)
        backend.arm_guarded_keyboard(*focus_point)
        frame = backend.guarded_keyboard_frame()
        frame_digest = _sha256_bytes(frame)
        receipt = backend.type_text_guarded(marker, expected_frame_sha256=frame_digest)
        result["keyboard_action_count"] += 1
        result["guarded_keyboard_delivery_pass"] = bool(
            receipt.operation == "physical_type_text"
            and receipt.native is False
            and receipt.outcome_verified is False
        )
        if not result["guarded_keyboard_delivery_pass"]:
            raise RuntimeError("guarded VS Code text delivery receipt failed contract")

        expected_after = {
            "exists": True,
            "size": len(marker_bytes),
            "sha256": _sha256_bytes(marker_bytes),
        }

        def artifact_saved() -> bool:
            return _artifact_evidence(target_file) == expected_after

        _wait_until(artifact_saved, timeout=10.0, label="VS Code autosave postcondition")
        after_artifact = _artifact_evidence(target_file)
        completion = verify_expected_fields(
            before=baseline,
            after=after_artifact,
            expectation=expected_after,
        )
        result["completion_verification_status"] = completion.status.value
        result["completion_verification_pass"] = completion.passed

        after_state = observe_bound_window(resolver, window_title)
        result["current_state_verification_pass"] = _same_window_identity(before_state, after_state)
        workspace_snapshot = _workspace_snapshot(workspace_root)
        result["workspace_snapshot"] = workspace_snapshot
        result["workspace_expected_only_pass"] = workspace_snapshot == {
            unique_filename: expected_after["sha256"]
        }
        result["resolver_stats"] = vars(resolver.stats).copy()

        result["pass"] = bool(
            result["application_discovery_pass"]
            and result["isolated_profile_pass"]
            and result["disposable_workspace_pass"]
            and result["preexisting_target_window_count"] == 0
            and result["window_binding_pass"]
            and result["desktop_observation_pass"]
            and result["focused_editor_precondition_pass"]
            and result["native_point_guard_pass"]
            and result["agent_loopback_pass"]
            and result["agent_auth_required_pass"]
            and result["legacy_capability_absent_pass"]
            and result["baseline_verification_status"] == VerificationStatus.PASS.value
            and result["mismatch_probe_verification_status"] == VerificationStatus.FAIL.value
            and result["mismatch_probe_zero_action_pass"]
            and result["guarded_keyboard_delivery_pass"]
            and result["keyboard_action_count"] == 1
            and result["current_state_verification_pass"]
            and result["completion_verification_pass"]
            and result["workspace_expected_only_pass"]
            and resolver.stats.desktop_fallback_calls == 0
            and resolver.stats.window_binding_failures == 0
            and resolver.stats.window_binding_ambiguities == 0
        )
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        result["resolver_stats"] = vars(resolver.stats).copy()
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
        if server_thread is not None:
            server_thread.join(timeout=5.0)

        if bound_hwnd is not None:
            try:
                _post_close(bound_hwnd)
                _wait_until(
                    lambda: not _matching_vscode_windows(unique_filename),
                    timeout=15.0,
                    label="isolated VS Code window close",
                )
                result["application_cleanup_pass"] = True
            except Exception:
                result["application_cleanup_pass"] = False
        else:
            result["application_cleanup_pass"] = not _matching_vscode_windows(unique_filename)

        if cli_process is not None:
            try:
                cli_process.wait(timeout=10.0)
            except subprocess.TimeoutExpired:
                cli_process.terminate()
                try:
                    cli_process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    cli_process.kill()
                    cli_process.wait(timeout=5.0)

        try:
            if app_root.exists():
                shutil.rmtree(app_root)
            result["app_root_cleanup_pass"] = not app_root.exists()
            result["rollback_pass"] = bool(
                result["application_cleanup_pass"] and result["app_root_cleanup_pass"]
            )
        except Exception:
            result["app_root_cleanup_pass"] = False
            result["rollback_pass"] = False

        result["pass"] = bool(
            result["pass"]
            and result["application_cleanup_pass"]
            and result["app_root_cleanup_pass"]
            and result["rollback_pass"]
        )
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("===== STAGE 26.2E VS CODE REAL APPLICATION E2E =====")
    print(f"RESULT_PATH={result_path}")
    for key in (
        "application_discovery_pass",
        "isolated_profile_pass",
        "disposable_workspace_pass",
        "preexisting_target_window_count",
        "window_title",
        "window_process_id",
        "window_binding_pass",
        "desktop_observation_pass",
        "focused_editor_precondition_pass",
        "focused_editor_role",
        "focused_editor_name",
        "native_point_guard_pass",
        "agent_loopback_pass",
        "agent_auth_required_pass",
        "legacy_capability_absent_pass",
        "baseline_verification_status",
        "mismatch_probe_verification_status",
        "mismatch_probe_decision",
        "mismatch_probe_zero_action_pass",
        "guarded_keyboard_delivery_pass",
        "keyboard_action_count",
        "current_state_verification_pass",
        "completion_verification_status",
        "completion_verification_pass",
        "workspace_expected_only_pass",
        "application_cleanup_pass",
        "app_root_cleanup_pass",
        "rollback_pass",
        "resolver_stats",
        "error",
        "pass",
    ):
        print(f"{key.upper()}={result.get(key)}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
