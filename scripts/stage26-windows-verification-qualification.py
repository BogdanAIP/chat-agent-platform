from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.control_plane.verification import VerificationStatus, verify_expected_effect
from runtime.control_plane.windows_observation import WindowsDesktopObservationStream
from runtime.control_plane.windows_transition import (
    build_windows_desktop_effect,
    verify_windows_desktop_transition,
)
from runtime.windows.observation import DesktopState, observe_bound_window
from runtime.windows.window_scoped_uia import WindowScopedUiaResolver


FIXTURE_WINDOW_NAME = "Stage 26 capture qualification fixture"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _wait_state(
    path: Path,
    predicate: Callable[[dict[str, Any]], bool],
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                last = _read_json(path)
            except Exception:
                last = {}
            if predicate(last):
                return last
        time.sleep(0.05)
    raise TimeoutError(f"timed out waiting for fixture state: {last}")


def _identity_tuple(state: DesktopState) -> tuple[Any, ...]:
    return (
        state.session_id,
        state.application_identity,
        state.executable_name,
        state.process_id,
        state.process_generation,
        state.window_handle,
        state.window_instance,
        state.coordinate_space,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--fixture-state", required=True)
    parser.add_argument("--recorder-ready", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    fixture_state_path = Path(args.fixture_state).resolve()
    ready_path = Path(args.recorder_ready).resolve()
    result_path = run_dir / "windows-verification-result.json"
    observation_adapter = REPO_ROOT / "runtime" / "control_plane" / "windows_observation.py"
    transition_adapter = REPO_ROOT / "runtime" / "control_plane" / "windows_transition.py"
    driver_path = Path(__file__).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "schema_version": 1,
        "qualification_kind": "shared-kernel-windows-desktop-verification",
        "observation_adapter_sha256": _sha256(observation_adapter),
        "transition_adapter_sha256": _sha256(transition_adapter),
        "driver_source_sha256": _sha256(driver_path),
        "fixture_process_id": None,
        "same_live_identity_pass": False,
        "kernel_pass_status": None,
        "kernel_pass_reason": None,
        "wrong_postcondition_status": None,
        "process_generation_drift_status": None,
        "hwnd_drift_status": None,
        "stale_observation_status": None,
        "identity_drift_fail_pass": False,
        "wrong_postcondition_fail_pass": False,
        "stale_unknown_pass": False,
        "resolver_stats": None,
        "pass": False,
        "error": None,
        "traceback": None,
    }

    try:
        ready_path.write_text("READY\n", encoding="ascii")
        fixture = _wait_state(
            fixture_state_path,
            lambda item: item.get("recorder_ready") is True and item.get("cycle_ready") is True,
        )
        fixture_pid = fixture.get("fixture_pid")
        if isinstance(fixture_pid, bool) or not isinstance(fixture_pid, int) or fixture_pid <= 0:
            raise RuntimeError("fixture did not publish a valid process id")
        result["fixture_process_id"] = fixture_pid

        resolver = WindowScopedUiaResolver()
        resolver.set_expected_process_id(fixture_pid)
        first = observe_bound_window(resolver, FIXTURE_WINDOW_NAME)
        second = observe_bound_window(resolver, FIXTURE_WINDOW_NAME)
        result["resolver_stats"] = vars(resolver.stats).copy()
        result["same_live_identity_pass"] = _identity_tuple(first) == _identity_tuple(second)

        expected = {"window": {"title": first.window_title}}
        verified = verify_windows_desktop_transition(
            before_raw=first.to_mapping(),
            after_raw=second.to_mapping(),
            expected=expected,
            subject=f"fixture-pid:{fixture_pid}",
            stream_id="physical-windows-verification",
            evidence_batch_id="physical-windows-verification",
        )
        result["kernel_pass_status"] = verified["status"]
        result["kernel_pass_reason"] = verified["verification"]["reason"]

        wrong = verify_windows_desktop_transition(
            before_raw=first.to_mapping(),
            after_raw=second.to_mapping(),
            expected={"window": {"title": first.window_title + " [wrong]"}},
            subject=f"fixture-pid:{fixture_pid}",
            stream_id="physical-windows-verification-wrong",
        )
        result["wrong_postcondition_status"] = wrong["status"]
        result["wrong_postcondition_fail_pass"] = wrong["status"] == "fail"

        generation_drift = copy.deepcopy(second.to_mapping())
        generation_drift["process_generation"] = second.process_generation + "-different"
        generation_drift["freshness_evidence"]["process_generation"] = generation_drift[
            "process_generation"
        ]
        generation = verify_windows_desktop_transition(
            before_raw=first.to_mapping(),
            after_raw=generation_drift,
            expected=expected,
            subject=f"fixture-pid:{fixture_pid}",
            stream_id="physical-windows-verification-generation",
        )
        result["process_generation_drift_status"] = generation["status"]

        hwnd_drift = copy.deepcopy(second.to_mapping())
        hwnd_drift["window_handle"] = second.window_handle + 1
        hwnd_drift["window_instance"] = "f" * 64
        hwnd_drift["freshness_evidence"]["window_handle"] = hwnd_drift["window_handle"]
        hwnd_drift["freshness_evidence"]["window_instance"] = hwnd_drift["window_instance"]
        hwnd = verify_windows_desktop_transition(
            before_raw=first.to_mapping(),
            after_raw=hwnd_drift,
            expected=expected,
            subject=f"fixture-pid:{fixture_pid}",
            stream_id="physical-windows-verification-hwnd",
        )
        result["hwnd_drift_status"] = hwnd["status"]
        result["identity_drift_fail_pass"] = bool(
            generation["status"] == "fail" and hwnd["status"] == "fail"
        )

        stream = WindowsDesktopObservationStream(
            subject=f"fixture-pid:{fixture_pid}",
            stream_id="physical-windows-verification-stale",
        )
        before = stream.observe(first.to_mapping())
        effect, _ = build_windows_desktop_effect(before=before, expected=expected)
        stale = verify_expected_effect(effect, before)
        result["stale_observation_status"] = stale.status.value
        result["stale_unknown_pass"] = stale.status is VerificationStatus.UNKNOWN

        stats = resolver.stats
        result["pass"] = bool(
            result["same_live_identity_pass"]
            and verified["status"] == "pass"
            and verified["verification"]["reason"] == "expected_effect_verified"
            and result["wrong_postcondition_fail_pass"]
            and result["identity_drift_fail_pass"]
            and result["stale_unknown_pass"]
            and first.process_id == fixture_pid
            and second.process_id == fixture_pid
            and stats.desktop_fallback_calls == 0
            and stats.window_binding_failures == 0
            and stats.window_binding_ambiguities == 0
        )
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()

    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("===== STAGE 26.3B WINDOWS VERIFICATION =====")
    print(f"RESULT_PATH={result_path}")
    print(f"OBSERVATION_ADAPTER_SHA256={result['observation_adapter_sha256']}")
    print(f"TRANSITION_ADAPTER_SHA256={result['transition_adapter_sha256']}")
    print(f"DRIVER_SOURCE_SHA256={result['driver_source_sha256']}")
    print(f"SAME_LIVE_IDENTITY_PASS={result['same_live_identity_pass']}")
    print(f"KERNEL_PASS_STATUS={result['kernel_pass_status']}")
    print(f"KERNEL_PASS_REASON={result['kernel_pass_reason']}")
    print(f"WRONG_POSTCONDITION_STATUS={result['wrong_postcondition_status']}")
    print(f"PROCESS_GENERATION_DRIFT_STATUS={result['process_generation_drift_status']}")
    print(f"HWND_DRIFT_STATUS={result['hwnd_drift_status']}")
    print(f"STALE_OBSERVATION_STATUS={result['stale_observation_status']}")
    print(f"IDENTITY_DRIFT_FAIL_PASS={result['identity_drift_fail_pass']}")
    print(f"WRONG_POSTCONDITION_FAIL_PASS={result['wrong_postcondition_fail_pass']}")
    print(f"STALE_UNKNOWN_PASS={result['stale_unknown_pass']}")
    print(f"ERROR={result['error']}")
    print(f"PASS={result['pass']}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
