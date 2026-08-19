from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import threading
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
BASELINE_PATH = SCRIPT_DIR / "stage26-windows-hot-runtime-benchmark.py"
RESOLVER_PATH = SCRIPT_DIR / "stage26-window-scoped-uia-resolver.py"
BASELINE_ACTION_P50_MS = 183606.855
BASELINE_ACTION_P95_MS = 185567.403
MINIMUM_SPEEDUP = 10.0


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


baseline = _load(BASELINE_PATH, "stage26_1d_baseline")
optimized = _load(RESOLVER_PATH, "stage26_1e_resolver")


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
    result_path = run_dir / "window-scoped-result.json"
    run_dir.mkdir(parents=True, exist_ok=True)

    total_cycles = args.warmup_cycles + args.measured_cycles
    # Eight structural resolutions per complete cycle plus one non-actuating
    # preflight lookup before any benchmark action is allowed.
    expected_scoped_calls = total_cycles * 8 + 1
    resolver = optimized.WindowScopedUiaResolver()
    result: dict[str, Any] = {
        "schema_version": 1,
        "benchmark_kind": "warm-window-scoped-native-uia",
        "warmup_cycles": args.warmup_cycles,
        "measured_cycles": args.measured_cycles,
        "total_cycles": total_cycles,
        "expected_window_scoped_find_calls": expected_scoped_calls,
        "preflight": {
            "window_binding_pass": False,
            "fixture_process_id": None,
            "candidate_count": None,
            "fingerprint_present": False,
        },
        "resolver_stats": {},
        "baseline_comparison": {
            "baseline_action_p50_ms": BASELINE_ACTION_P50_MS,
            "baseline_action_p95_ms": BASELINE_ACTION_P95_MS,
            "minimum_speedup": MINIMUM_SPEEDUP,
            "p50_speedup": None,
            "p95_speedup": None,
            "minimum_speedup_pass": False,
        },
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

    token = baseline.accepted.secrets.token_urlsafe(32)
    server = None
    thread: threading.Thread | None = None

    try:
        config = baseline.AgentConfig(
            host="127.0.0.1",
            port=0,
            token=token,
            allow_legacy_exec=False,
        )
        server = baseline.create_server(
            config,
            input_fn=baseline.accepted._qualification_input,
            uia_fn=resolver.perform,
        )
        host, port = server.server_address[:2]
        if str(host) != "127.0.0.1" or int(port) <= 0:
            raise RuntimeError("optimized benchmark agent was not loopback-bound")

        thread = threading.Thread(
            target=server.serve_forever,
            name="stage26-1e-window-scoped-uia-agent",
            daemon=True,
        )
        thread.start()
        base_url = f"http://127.0.0.1:{int(port)}"

        health = baseline.accepted.requests.get(f"{base_url}/health", timeout=10.0)
        health.raise_for_status()
        health_data = health.json()
        if health_data.get("auth_required") is not True:
            raise RuntimeError("optimized benchmark agent auth unexpectedly disabled")
        if "legacy_exec" in (health_data.get("capabilities") or []):
            raise RuntimeError("legacy exec unexpectedly enabled")

        backend = baseline.WindowsBackend(
            server_url=base_url,
            auth_token=token,
            require_tls=False,
            allow_legacy_exec=False,
        )

        ready_path.write_text("READY\n", encoding="ascii")
        initial = baseline._wait_state(
            fixture_state_path,
            lambda item: item.get("recorder_ready") is True,
            label="optimized benchmark fixture recorder_ready",
        )
        fixture_pid = initial.get("fixture_pid")
        if isinstance(fixture_pid, bool) or not isinstance(fixture_pid, int) or fixture_pid <= 0:
            raise RuntimeError("fixture did not publish a valid process id")

        resolver.set_expected_process_id(fixture_pid)

        # Non-actuating fail-fast preflight. No benchmark cycle is started until
        # the exact fixture process/window and Start button resolve uniquely.
        preflight_locator = baseline.accepted._structural(
            "button",
            "Stage 26 start button",
        )
        preflight_handle = baseline.accepted._resolve_unique(
            backend,
            preflight_locator,
        )
        result["preflight"] = {
            "window_binding_pass": True,
            "fixture_process_id": fixture_pid,
            "candidate_count": preflight_handle.candidate_count,
            "fingerprint_present": bool(preflight_handle.target_fingerprint),
        }

        cycle = 1
        for _ in range(args.warmup_cycles):
            baseline._run_cycle(
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
            samples.append(
                baseline._run_cycle(
                    backend=backend,
                    base_url=base_url,
                    token=token,
                    fixture_state_path=fixture_state_path,
                    cycle_number=cycle,
                    record_metrics=True,
                )
            )
            cycle += 1

        final_state = baseline._wait_state(
            fixture_state_path,
            lambda item: item.get("benchmark_done") is True,
            label="optimized benchmark fixture done",
        )
        result["samples"] = samples
        result["fixture_state"] = final_state
        result["agent_process_reused"] = True
        result["fixture_process_reused"] = (
            fixture_pid is not None and final_state.get("fixture_pid") == fixture_pid
        )

        metric_names = sorted(samples[0]["metrics"])
        result["summary"] = {
            metric: baseline._summary(
                [float(sample["metrics"][metric]) for sample in samples]
            )
            for metric in metric_names
        }
        result["resolver_stats"] = asdict(resolver.stats)

        action_summary = result["summary"]["action_sequence_total_ms"]
        p50_speedup = BASELINE_ACTION_P50_MS / float(action_summary["p50_ms"])
        p95_speedup = BASELINE_ACTION_P95_MS / float(action_summary["p95_ms"])
        speedup_pass = p50_speedup >= MINIMUM_SPEEDUP and p95_speedup >= MINIMUM_SPEEDUP
        result["baseline_comparison"] = {
            "baseline_action_p50_ms": BASELINE_ACTION_P50_MS,
            "baseline_action_p95_ms": BASELINE_ACTION_P95_MS,
            "minimum_speedup": MINIMUM_SPEEDUP,
            "p50_speedup": round(p50_speedup, 3),
            "p95_speedup": round(p95_speedup, 3),
            "minimum_speedup_pass": speedup_pass,
        }

        result["pass"] = bool(
            result["preflight"]["window_binding_pass"]
            and result["preflight"]["candidate_count"] == 1
            and result["preflight"]["fingerprint_present"]
            and len(samples) == args.measured_cycles
            and int(final_state.get("completed_cycles", 0)) == total_cycles
            and result["agent_process_reused"]
            and result["fixture_process_reused"]
            and resolver.stats.window_scoped_find_calls == expected_scoped_calls
            and resolver.stats.desktop_fallback_calls == 0
            and resolver.stats.window_binding_failures == 0
            and resolver.stats.window_binding_ambiguities == 0
            and result["unrelated_window_action_count"] == 0
            and result["false_action_count"] == 0
            and speedup_pass
            and all(
                sample["delivered_operations"] == baseline.EXPECTED_OPERATIONS
                for sample in samples
            )
        )
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        result["resolver_stats"] = asdict(resolver.stats)
        if fixture_state_path.is_file():
            try:
                result["fixture_state"] = baseline._read_json(fixture_state_path)
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

    print("===== STAGE 26.1E WINDOW-SCOPED UIA BENCHMARK =====")
    print(f"BENCHMARK_KIND={result['benchmark_kind']}")
    print(f"WARMUP_CYCLES={result['warmup_cycles']}")
    print(f"MEASURED_CYCLES={result['measured_cycles']}")
    preflight = result.get("preflight", {})
    print(f"WINDOW_BINDING_PASS={preflight.get('window_binding_pass')}")
    print(f"PREFLIGHT_CANDIDATE_COUNT={preflight.get('candidate_count')}")
    print(f"PREFLIGHT_FINGERPRINT_PRESENT={preflight.get('fingerprint_present')}")
    stats = result.get("resolver_stats", {})
    for key in (
        "window_scoped_find_calls",
        "desktop_fallback_calls",
        "delegated_uia_calls",
        "automation_id_condition_calls",
        "role_name_condition_calls",
        "window_enum_calls",
        "window_enum_handles_seen",
        "process_window_handles_seen",
        "window_uia_convertible_count",
        "window_name_match_count",
        "window_binding_failures",
        "window_binding_ambiguities",
    ):
        print(f"{key.upper()}={stats.get(key)}")
    comparison = result.get("baseline_comparison", {})
    print(f"P50_SPEEDUP={comparison.get('p50_speedup')}")
    print(f"P95_SPEEDUP={comparison.get('p95_speedup')}")
    print(f"MINIMUM_SPEEDUP={comparison.get('minimum_speedup')}")
    print(f"MINIMUM_SPEEDUP_PASS={comparison.get('minimum_speedup_pass')}")
    for metric, summary in result.get("summary", {}).items():
        label = metric.upper()
        if label.endswith("_MS"):
            label = label[:-3]
        print(f"{label}_P50_MS={summary['p50_ms']}")
        print(f"{label}_P95_MS={summary['p95_ms']}")
    print(f"ERROR={result.get('error')}")
    print(f"PASS={result.get('pass')}")
    print(f"WINDOW_SCOPED_RESULT_PATH={result_path}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
