from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import traceback
from importlib import metadata
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
from runtime.windows.observation import DesktopState, build_desktop_state, observe_bound_window
from runtime.windows.window_scoped_uia import WindowScopedUiaResolver, _upstream


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


def _control_inputs(state: DesktopState) -> list[dict[str, Any]]:
    return [
        {
            "role": control.role,
            "name": control.name,
            "automation_id": control.automation_id,
            "bounds": control.bounds.to_mapping() if control.bounds is not None else None,
            "enabled": control.enabled,
            "visible": control.visible,
            "focused": control.focused,
        }
        for control in state.controls
    ]


def _identity_variant(
    state: DesktopState,
    *,
    process_generation: str | None = None,
    window_handle: int | None = None,
) -> dict[str, Any]:
    """Build a canonical synthetic negative probe with internally valid digests."""

    variant = build_desktop_state(
        session_id=state.session_id,
        application_identity=state.application_identity,
        executable_name=state.executable_name,
        process_id=state.process_id,
        process_generation=process_generation or state.process_generation,
        window_handle=window_handle or state.window_handle,
        window_title=state.window_title,
        window_bounds=state.window_bounds,
        controls=_control_inputs(state),
        observed_at=state.observed_at,
        focus_evidence={"qualification_probe": "synthetic_identity_variant"},
    )
    return variant.to_mapping()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _openadapt_attestation() -> dict[str, Any]:
    """Bind the installed UIA backend used by this physical run to the project pin.

    SourceProvenanceGate binds the lockfile inside the exact Git tree. This
    record additionally captures the actual installed distribution version and
    the SHA-256 of the win_agent server module imported by the resolver.
    """

    lock_path = REPO_ROOT / "config" / "stage26-openadapt-lock.json"
    lock = _read_json(lock_path)
    expected_version = str(lock["upstreams"]["openadapt_flow"]["declared_version"])
    expected_commit = str(lock["upstreams"]["openadapt_flow"]["commit"])
    installed_version = metadata.version("openadapt-flow")
    server = _upstream()
    server_file_raw = getattr(server, "__file__", None)
    if not server_file_raw:
        raise RuntimeError("OpenAdapt win_agent server module has no source path")
    server_path = Path(server_file_raw).resolve()
    if not server_path.is_file():
        raise RuntimeError(f"OpenAdapt win_agent server source is missing: {server_path}")
    return {
        "lockfile": str(lock_path),
        "lockfile_sha256": _sha256(lock_path),
        "repository": str(lock["upstreams"]["openadapt_flow"]["repository"]),
        "expected_commit": expected_commit,
        "expected_version": expected_version,
        "installed_version": installed_version,
        "version_match": installed_version == expected_version,
        "win_agent_server_path": str(server_path),
        "win_agent_server_sha256": _sha256(server_path),
    }


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
        "openadapt_attestation": None,
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
        attestation = _openadapt_attestation()
        result["openadapt_attestation"] = attestation
        if not attestation["version_match"]:
            raise RuntimeError(
                "installed openadapt-flow does not match project lock: "
                f"expected={attestation['expected_version']} actual={attestation['installed_version']}"
            )

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

        generation = verify_windows_desktop_transition(
            before_raw=first.to_mapping(),
            after_raw=_identity_variant(
                second,
                process_generation=second.process_generation + "-different",
            ),
            expected=expected,
            subject=f"fixture-pid:{fixture_pid}",
            stream_id="physical-windows-verification-generation",
        )
        result["process_generation_drift_status"] = generation["status"]

        hwnd = verify_windows_desktop_transition(
            before_raw=first.to_mapping(),
            after_raw=_identity_variant(second, window_handle=second.window_handle + 1),
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
            attestation["version_match"]
            and result["same_live_identity_pass"]
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
    if result["openadapt_attestation"] is not None:
        attestation = result["openadapt_attestation"]
        print(f"OPENADAPT_EXPECTED_VERSION={attestation['expected_version']}")
        print(f"OPENADAPT_INSTALLED_VERSION={attestation['installed_version']}")
        print(f"OPENADAPT_VERSION_MATCH={attestation['version_match']}")
        print(f"OPENADAPT_WIN_AGENT_SERVER_SHA256={attestation['win_agent_server_sha256']}")
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
