from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable

from openadapt_flow.backends.windows_backend import WindowsBackend
from openadapt_flow.backends.win_agent.server import AgentConfig, create_server


SCRIPT_DIR = Path(__file__).resolve().parent
ACCEPTED_DRIVER_PATH = SCRIPT_DIR / "stage26-openadapt-windows-executor-driver.py"
FIXTURE_WINDOW_NAME = "Stage 26 capture qualification fixture"
EXPECTED_OPERATIONS = [
    "uia_invoke",
    "uia_focus",
    "physical_type_text",
    "physical_press",
    "physical_click",
    "physical_scroll",
    "uia_invoke",
]


def _load_accepted_driver():
    spec = importlib.util.spec_from_file_location(
        "stage26_1c_accepted_executor", ACCEPTED_DRIVER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load accepted Stage 26.1C executor driver")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


accepted = _load_accepted_driver()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _wait_until(
    predicate: Callable[[], bool],
    *,
    timeout: float,
    label: str,
    interval: float = 0.02,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise TimeoutError(f"timed out waiting for {label}")


def _wait_state(
    path: Path,
    predicate: Callable[[dict[str, Any]], bool],
    *,
    timeout: float = 10.0,
    label: str,
) -> dict[str, Any]:
    state: dict[str, Any] = {}

    def ready() -> bool:
        nonlocal state
        if not path.is_file():
            return False
        try:
            state = _read_json(path)
        except Exception:
            return False
        return predicate(state)

    _wait_until(ready, timeout=timeout, label=label)
    return state


def _ms(start_ns: int) -> float:
    return round((time.perf_counter_ns() - start_ns) / 1_000_000.0, 3)


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("percentile needs at least one sample")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1))
    return float(ordered[index])


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "min_ms": round(min(values), 3),
        "p50_ms": round(float(statistics.median(values)), 3),
        "p95_ms": round(_percentile(values, 0.95), 3),
        "max_ms": round(max(values), 3),
        "mean_ms": round(float(statistics.fmean(values)), 3),
    }


def _fixture_expected_text(state: dict[str, Any]) -> str:
    value = state.get("expected_text")
    if not isinstance(value, str) or not value:
        raise RuntimeError("fixture omitted expected_text")
    return value


def _run_cycle(
    *,
    backend: WindowsBackend,
    base_url: str,
    token: str,
    fixture_state_path: Path,
    cycle_number: int,
    record_metrics: bool,
) -> dict[str, Any]:
    state = _wait_state(
        fixture_state_path,
        lambda item: (
            item.get("benchmark_done") is not True
            and item.get("current_iteration") == cycle_number
            and item.get("cycle_ready") is True
        ),
        label=f"fixture cycle {cycle_number} ready",
    )
    expected_text = _fixture_expected_text(state)
    metrics: dict[str, float] = {}
    delivered: list[str] = []

    action_sequence_start = time.perf_counter_ns()

    start_locator = accepted._structural("button", "Stage 26 start button")
    phase = time.perf_counter_ns()
    start_handle = accepted._resolve_unique(backend, start_locator)
    start_receipt = backend.act_structural(start_locator, start_handle)
    delivered.append(start_receipt.operation)
    _wait_state(
        fixture_state_path,
        lambda item: item.get("start_clicked") is True,
        label=f"cycle {cycle_number} start_clicked",
    )
    metrics["start_uia_ms"] = _ms(phase)

    textbox_locator = accepted._structural("textbox", "Stage 26 capture input")
    phase = time.perf_counter_ns()
    textbox_point, textbox_operation = accepted._act_native(backend, textbox_locator)
    delivered.append(textbox_operation)
    metrics["focus_uia_ms"] = _ms(phase)

    phase = time.perf_counter_ns()
    type_receipt = accepted._guarded_keyboard(
        backend,
        textbox_point,
        lambda digest: backend.type_text_guarded(
            expected_text,
            expected_frame_sha256=digest,
        ),
    )
    delivered.append(type_receipt.operation)
    typed_state = _wait_state(
        fixture_state_path,
        lambda item: item.get("text_ok") is True,
        label=f"cycle {cycle_number} text_ok",
    )
    if typed_state.get("text_value") != expected_text:
        raise RuntimeError("fixture text did not match expected benchmark text")
    metrics["guarded_type_ms"] = _ms(phase)

    textbox_handle = accepted._resolve_unique(backend, textbox_locator)
    textbox_point = (int(textbox_handle.point[0]), int(textbox_handle.point[1]))
    phase = time.perf_counter_ns()
    press_receipt = accepted._guarded_keyboard(
        backend,
        textbox_point,
        lambda digest: backend.press_guarded(
            "Enter",
            expected_frame_sha256=digest,
        ),
    )
    delivered.append(press_receipt.operation)
    _wait_state(
        fixture_state_path,
        lambda item: item.get("enter_pressed") is True,
        label=f"cycle {cycle_number} enter_pressed",
    )
    metrics["guarded_press_ms"] = _ms(phase)

    row_locator = accepted._structural("listitem", "Qualification row 01")
    phase = time.perf_counter_ns()
    row_handle = accepted._resolve_unique(backend, row_locator)
    metrics["row_uia_find_ms"] = _ms(phase)
    row_point = (int(row_handle.point[0]), int(row_handle.point[1]))

    phase = time.perf_counter_ns()
    click_receipt = accepted._guarded_coordinate(backend, row_point)
    delivered.append(click_receipt.operation)
    metrics["guarded_click_ms"] = _ms(phase)

    phase = time.perf_counter_ns()
    scroll_receipt = accepted._guarded_scroll_raw(
        base_url,
        token,
        backend,
        vertical_notches=-3,
    )
    delivered.append(str(scroll_receipt.get("operation")))
    _wait_state(
        fixture_state_path,
        lambda item: item.get("scroll_seen") is True,
        label=f"cycle {cycle_number} scroll_seen",
    )
    metrics["guarded_scroll_ms"] = _ms(phase)

    finish_locator = accepted._structural("button", "Stage 26 finish button")
    phase = time.perf_counter_ns()
    finish_handle = accepted._resolve_unique(backend, finish_locator)
    finish_receipt = backend.act_structural(finish_locator, finish_handle)
    delivered.append(finish_receipt.operation)
    final_state = _wait_state(
        fixture_state_path,
        lambda item: int(item.get("completed_cycles", 0)) >= cycle_number,
        label=f"cycle {cycle_number} completed",
    )
    metrics["finish_uia_ms"] = _ms(phase)
    metrics["action_sequence_total_ms"] = _ms(action_sequence_start)

    if delivered != EXPECTED_OPERATIONS:
        raise RuntimeError(
            f"cycle {cycle_number} operation sequence drifted: {delivered!r}"
        )
    if int(final_state.get("completed_cycles", 0)) < cycle_number:
        raise RuntimeError(f"fixture failed to commit cycle {cycle_number}")

    return {
        "cycle": cycle_number,
        "expected_text": expected_text,
        "delivered_operations": delivered,
        "metrics": metrics if record_metrics else {},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--fixture-state", required=True)
    parser.add_argument("--recorder-ready", required=True)
    parser.add_argument("--warmup-cycles", type=int, default=2)
    parser.add_argument("--measured-cycles", type=int, default=10)
    args = parser.parse_args()

    if not 0 <= args.warmup_cycles <= 10:
        parser.error("--warmup-cycles must be between 0 and 10")
    if not 3 <= args.measured_cycles <= 50:
        parser.error("--measured-cycles must be between 3 and 50")

    run_dir = Path(args.run_dir).resolve()
    fixture_state_path = Path(args.fixture_state).resolve()
    ready_path = Path(args.recorder_ready).resolve()
    result_path = run_dir / "hot-runtime-result.json"
    run_dir.mkdir(parents=True, exist_ok=True)

    total_cycles = args.warmup_cycles + args.measured_cycles
    result: dict[str, Any] = {
        "schema_version": 1,
        "benchmark_kind": "warm-single-process-uia-first",
        "warmup_cycles": args.warmup_cycles,
        "measured_cycles": args.measured_cycles,
        "total_cycles": total_cycles,
        "latency_budget_enforced": False,
        "agent_bind_host": None,
        "agent_port": None,
        "agent_process_reused": False,
        "fixture_process_reused": False,
        "samples": [],
        "summary": {},
        "fixture_state": None,
        "unrelated_window_action_count": 0,
        "false_action_count": 0,
        "pass": False,
        "error": None,
        "traceback": None,
    }

    server = None
    thread = None
    token = accepted.secrets.token_urlsafe(32)

    try:
        config = AgentConfig(
            host="127.0.0.1",
            port=0,
            token=token,
            allow_legacy_exec=False,
        )
        server = create_server(config, input_fn=accepted._qualification_input)
        host, port = server.server_address[:2]
        result["agent_bind_host"] = str(host)
        result["agent_port"] = int(port)
        if str(host) != "127.0.0.1" or int(port) <= 0:
            raise RuntimeError("benchmark agent was not loopback-bound")

        thread = accepted.threading.Thread(
            target=server.serve_forever,
            name="stage26-1d-hot-runtime-agent",
            daemon=True,
        )
        thread.start()
        base_url = f"http://127.0.0.1:{int(port)}"

        health = accepted.requests.get(f"{base_url}/health", timeout=10.0)
        health.raise_for_status()
        health_data = health.json()
        if health_data.get("auth_required") is not True:
            raise RuntimeError("benchmark agent auth unexpectedly disabled")
        if "legacy_exec" in (health_data.get("capabilities") or []):
            raise RuntimeError("legacy exec unexpectedly enabled")

        backend = WindowsBackend(
            server_url=base_url,
            auth_token=token,
            require_tls=False,
            allow_legacy_exec=False,
        )

        ready_path.write_text("READY\n", encoding="ascii")
        initial = _wait_state(
            fixture_state_path,
            lambda item: item.get("recorder_ready") is True,
            label="benchmark fixture recorder_ready",
        )
        initial_fixture_pid = initial.get("fixture_pid")

        cycle = 1
        for _ in range(args.warmup_cycles):
            _run_cycle(
                backend=backend,
                base_url=base_url,
                token=token,
                fixture_state_path=fixture_state_path,
                cycle_number=cycle,
                record_metrics=False,
            )
            cycle += 1

        samples: list[dict[str, Any]] = []
        for _ in range(args.measured_cycles):
            sample = _run_cycle(
                backend=backend,
                base_url=base_url,
                token=token,
                fixture_state_path=fixture_state_path,
                cycle_number=cycle,
                record_metrics=True,
            )
            samples.append(sample)
            cycle += 1

        final_state = _wait_state(
            fixture_state_path,
            lambda item: item.get("benchmark_done") is True,
            label="benchmark fixture done",
        )
        result["fixture_state"] = final_state
        result["samples"] = samples
        result["agent_process_reused"] = True
        result["fixture_process_reused"] = (
            initial_fixture_pid is not None
            and final_state.get("fixture_pid") == initial_fixture_pid
        )

        metric_names = sorted(samples[0]["metrics"])
        result["summary"] = {
            metric: _summary(
                [float(sample["metrics"][metric]) for sample in samples]
            )
            for metric in metric_names
        }

        result["pass"] = bool(
            len(samples) == args.measured_cycles
            and int(final_state.get("completed_cycles", 0)) == total_cycles
            and result["agent_process_reused"]
            and result["fixture_process_reused"]
            and result["unrelated_window_action_count"] == 0
            and result["false_action_count"] == 0
            and all(
                sample["delivered_operations"] == EXPECTED_OPERATIONS
                for sample in samples
            )
        )
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        if fixture_state_path.is_file():
            try:
                result["fixture_state"] = _read_json(fixture_state_path)
            except Exception:
                pass
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
        if thread is not None:
            thread.join(timeout=5.0)
        result_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print("===== STAGE 26.1D WINDOWS HOT RUNTIME BENCHMARK =====")
    for key in (
        "benchmark_kind",
        "warmup_cycles",
        "measured_cycles",
        "agent_bind_host",
        "agent_port",
        "agent_process_reused",
        "fixture_process_reused",
        "latency_budget_enforced",
        "unrelated_window_action_count",
        "false_action_count",
        "error",
        "pass",
    ):
        print(f"{key.upper()}={result.get(key)}")
    for metric, summary in result.get("summary", {}).items():
        label = metric.upper()
        print(f"{label}_P50_MS={summary['p50_ms']}")
        print(f"{label}_P95_MS={summary['p95_ms']}")
    print(f"HOT_RUNTIME_RESULT_PATH={result_path}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
