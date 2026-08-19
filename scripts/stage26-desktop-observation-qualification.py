from __future__ import annotations

import argparse
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

from runtime.windows.observation import DesktopState, Rect, observe_bound_window
from runtime.windows.window_scoped_uia import WindowScopedUiaResolver


FIXTURE_WINDOW_NAME = "Stage 26 capture qualification fixture"
EXPECTED_CONTROL_NAMES = {
    "Stage 26 start button",
    "Stage 26 capture input",
    "Stage 26 finish button",
    "Qualification row 01",
}


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


def _capture_exact_window(bounds: Rect) -> bytes:
    if bounds.width <= 0 or bounds.height <= 0:
        raise RuntimeError("window bounds are empty")

    import mss
    import mss.tools

    monitor = {
        "left": bounds.left,
        "top": bounds.top,
        "width": bounds.width,
        "height": bounds.height,
    }
    with mss.mss() as capture:
        shot = capture.grab(monitor)
        return mss.tools.to_png(shot.rgb, shot.size)


def _control_names(state: DesktopState) -> set[str]:
    return {control.name for control in state.controls if control.name}


def _identity_tuple(state: DesktopState) -> tuple[Any, ...]:
    return (
        state.session_id,
        state.application_identity,
        state.executable_name,
        state.process_id,
        state.process_generation,
        state.window_handle,
        state.window_instance,
        state.window_title,
        state.window_bounds,
        state.coordinate_space,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--fixture-state", required=True)
    parser.add_argument("--recorder-ready", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    fixture_state_path = Path(args.fixture_state).resolve()
    ready_path = Path(args.recorder_ready).resolve()
    result_path = run_dir / "desktop-observation-result.json"
    run_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "schema_version": 1,
        "qualification_kind": "read-only-production-desktop-state",
        "production_observation_path": str(REPO_ROOT / "runtime" / "windows" / "observation.py"),
        "production_resolver_path": str(REPO_ROOT / "runtime" / "windows" / "window_scoped_uia.py"),
        "fixture_process_id": None,
        "first_state": None,
        "second_state": None,
        "same_identity_pass": False,
        "control_contract_pass": False,
        "screenshot_digest_pass": False,
        "freshness_contract_pass": False,
        "bounded_control_count_pass": False,
        "observation_only_pass": True,
        "action_count": 0,
        "false_action_count": 0,
        "unrelated_window_action_count": 0,
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
        screenshot = _capture_exact_window(first.window_bounds)
        second = observe_bound_window(
            resolver,
            FIXTURE_WINDOW_NAME,
            screenshot_png=screenshot,
            screenshot_source="mss_exact_bound_window",
        )

        result["first_state"] = first.to_mapping()
        result["second_state"] = second.to_mapping()
        result["resolver_stats"] = vars(resolver.stats).copy()

        names = _control_names(second)
        result["same_identity_pass"] = _identity_tuple(first) == _identity_tuple(second)
        result["control_contract_pass"] = EXPECTED_CONTROL_NAMES.issubset(names)
        result["screenshot_digest_pass"] = bool(
            second.screenshot_digest
            and len(second.screenshot_digest) == 64
            and "screenshot_digest" in second.observation_source
            and "screenshot_digest" in second.observed_capabilities
        )
        result["freshness_contract_pass"] = bool(
            len(second.frame_digest) == 64
            and len(second.window_instance) == 64
            and second.freshness_evidence.get("window_instance") == second.window_instance
            and second.freshness_evidence.get("screenshot_digest") == second.screenshot_digest
            and second.process_generation
        )
        result["bounded_control_count_pass"] = 0 < len(second.controls) <= 512

        result["pass"] = bool(
            result["same_identity_pass"]
            and result["control_contract_pass"]
            and result["screenshot_digest_pass"]
            and result["freshness_contract_pass"]
            and result["bounded_control_count_pass"]
            and result["observation_only_pass"]
            and result["action_count"] == 0
            and result["false_action_count"] == 0
            and result["unrelated_window_action_count"] == 0
            and second.process_id == fixture_pid
            and second.window_handle > 0
            and second.session_id.startswith("windows-session:")
            and second.application_identity.startswith("sha256:")
            and second.coordinate_space == "screen_physical_px"
            and resolver.stats.desktop_fallback_calls == 0
            and resolver.stats.window_binding_failures == 0
            and resolver.stats.window_binding_ambiguities == 0
        )
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()

    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("===== STAGE 26.2B DESKTOP OBSERVATION =====")
    print(f"RESULT_PATH={result_path}")
    print(f"SAME_IDENTITY_PASS={result['same_identity_pass']}")
    print(f"CONTROL_CONTRACT_PASS={result['control_contract_pass']}")
    print(f"SCREENSHOT_DIGEST_PASS={result['screenshot_digest_pass']}")
    print(f"FRESHNESS_CONTRACT_PASS={result['freshness_contract_pass']}")
    print(f"BOUNDED_CONTROL_COUNT_PASS={result['bounded_control_count_pass']}")
    print(f"OBSERVATION_ONLY_PASS={result['observation_only_pass']}")
    print(f"ACTION_COUNT={result['action_count']}")
    print(f"FALSE_ACTION_COUNT={result['false_action_count']}")
    print(f"UNRELATED_WINDOW_ACTION_COUNT={result['unrelated_window_action_count']}")
    print(f"ERROR={result['error']}")
    print(f"PASS={result['pass']}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
