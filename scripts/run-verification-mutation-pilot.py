from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "tests" / "mutation" / "verification_guarantees.json"
_DETECTOR_MARKER = "CAP_MUTATION_DETECTOR_RESULT="
_DETECTOR_SCRIPT = r'''
import json
import sys
import unittest
from pathlib import Path

import runtime.control_plane.verification as verification_module

selector = sys.argv[1]
suite = unittest.defaultTestLoader.loadTestsFromName(selector)
result = unittest.TestResult()
suite.run(result)

payload = {
    "selector": selector,
    "tests_run": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "skipped": len(result.skipped),
    "expected_failures": len(result.expectedFailures),
    "unexpected_successes": len(result.unexpectedSuccesses),
    "failure_test_ids": [case.id() for case, _ in result.failures],
    "error_test_ids": [case.id() for case, _ in result.errors],
    "verification_module_path": str(Path(verification_module.__file__).resolve()),
}
print("CAP_MUTATION_DETECTOR_RESULT=" + json.dumps(payload, sort_keys=True))
'''


def _load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported mutation manifest schema_version")
    mutants = data.get("mutants")
    if not isinstance(mutants, list) or not mutants:
        raise ValueError("mutation manifest must contain a non-empty mutants list")
    return data


def _prepare_overlay(target_relative: str) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
    temp = tempfile.TemporaryDirectory(prefix="cap-m0-mutant-")
    overlay = Path(temp.name)
    source_control_plane = ROOT / "runtime" / "control_plane"
    overlay_control_plane = overlay / "runtime" / "control_plane"
    shutil.copytree(source_control_plane, overlay_control_plane)
    target = overlay / target_relative
    if not target.is_file():
        temp.cleanup()
        raise FileNotFoundError(f"mutation target not present in overlay: {target_relative}")
    return temp, overlay, target


def _test_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _run_suite(overlay: Path, test_modules: list[str], *, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "unittest", *test_modules]
    return subprocess.run(
        command,
        cwd=overlay,
        env=_test_environment(),
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )


def _run_detector(overlay: Path, detector_test: str, *, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-c", _DETECTOR_SCRIPT, detector_test]
    return subprocess.run(
        command,
        cwd=overlay,
        env=_test_environment(),
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )


def _apply_mutation(source: str, *, find: str, replace: str, mutant_id: str) -> str:
    count = source.count(find)
    if count != 1:
        raise ValueError(f"{mutant_id} anchor matched {count} times; expected exactly 1")
    return source.replace(find, replace, 1)


def _tail(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _parse_detector_payload(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    if completed.returncode != 0:
        raise ValueError(f"detector process exited non-zero: {completed.returncode}")
    matches = [
        line[len(_DETECTOR_MARKER) :]
        for line in completed.stdout.splitlines()
        if line.startswith(_DETECTOR_MARKER)
    ]
    if len(matches) != 1:
        raise ValueError(f"detector emitted {len(matches)} structured result markers; expected exactly 1")
    payload = json.loads(matches[0])
    if not isinstance(payload, dict):
        raise ValueError("detector structured result must be an object")
    return payload


def _classify_detector_payload(payload: dict[str, Any], *, detector_test: str) -> tuple[str, str]:
    if payload.get("selector") != detector_test:
        return "error", "detector_selector_mismatch"

    integer_fields = (
        "tests_run",
        "failures",
        "errors",
        "skipped",
        "expected_failures",
        "unexpected_successes",
    )
    if any(type(payload.get(field)) is not int for field in integer_fields):
        return "error", "detector_result_schema_invalid"

    if payload["tests_run"] != 1:
        return "error", "detector_did_not_run_exactly_one_test"
    if payload["errors"] != 0:
        return "error", "detector_test_errored"
    if payload["skipped"] != 0:
        return "error", "detector_test_skipped"
    if payload["expected_failures"] != 0 or payload["unexpected_successes"] != 0:
        return "error", "detector_test_used_nonstandard_outcome"

    if payload["failures"] == 1:
        return "killed", "named_detector_assertion_failed"
    if payload["failures"] == 0:
        return "survived", "named_detector_passed"
    return "error", "detector_reported_multiple_failures"


def _detector_bound_to_target(payload: dict[str, Any], *, target: Path) -> bool:
    raw_path = payload.get("verification_module_path")
    if not isinstance(raw_path, str) or not raw_path:
        return False
    try:
        actual = Path(raw_path).resolve()
    except (OSError, RuntimeError):
        return False
    return actual == target.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the CAP-M0 curated Verification Kernel mutation pilot.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = _load_manifest(manifest_path)
    target_relative = manifest["target"]
    test_modules = manifest["test_modules"]
    if not isinstance(target_relative, str) or not target_relative:
        raise ValueError("manifest target must be a non-empty string")
    if not isinstance(test_modules, list) or not test_modules or any(type(item) is not str for item in test_modules):
        raise ValueError("manifest test_modules must be a non-empty string list")

    for mutant in manifest["mutants"]:
        detector_test = mutant.get("detector_test")
        if not isinstance(detector_test, str) or not detector_test.startswith("tests."):
            raise ValueError(f"{mutant.get('id')} detector_test must be an exact unittest selector under tests.*")

    baseline_temp, baseline_overlay, _ = _prepare_overlay(target_relative)
    try:
        baseline = _run_suite(
            baseline_overlay,
            test_modules,
            timeout_seconds=args.timeout_seconds,
        )
    finally:
        baseline_temp.cleanup()

    report: dict[str, Any] = {
        "suite": manifest.get("suite"),
        "target": target_relative,
        "baseline": {
            "status": "pass" if baseline.returncode == 0 else "fail",
            "returncode": baseline.returncode,
            "stdout_tail": _tail(baseline.stdout),
            "stderr_tail": _tail(baseline.stderr),
        },
        "mutants": [],
    }

    if baseline.returncode != 0:
        print("CAP_M0_BASELINE=FAIL")
        print(_tail(baseline.stdout))
        print(_tail(baseline.stderr), file=sys.stderr)
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 2

    print("CAP_M0_BASELINE=PASS")

    for mutant in manifest["mutants"]:
        mutant_id = mutant["id"]
        detector_test = mutant["detector_test"]
        started = time.monotonic()
        temp, overlay, target = _prepare_overlay(target_relative)
        try:
            original = target.read_text(encoding="utf-8")
            mutated = _apply_mutation(
                original,
                find=mutant["find"],
                replace=mutant["replace"],
                mutant_id=mutant_id,
            )
            target.write_text(mutated, encoding="utf-8")
            try:
                py_compile.compile(str(target), doraise=True)
            except py_compile.PyCompileError as exc:
                outcome = {
                    "id": mutant_id,
                    "name": mutant["name"],
                    "guarantee": mutant["guarantee"],
                    "detector_test": detector_test,
                    "status": "error",
                    "reason": "mutated_target_did_not_compile",
                    "detail": str(exc),
                }
            else:
                try:
                    completed = _run_detector(
                        overlay,
                        detector_test,
                        timeout_seconds=args.timeout_seconds,
                    )
                except subprocess.TimeoutExpired as exc:
                    outcome = {
                        "id": mutant_id,
                        "name": mutant["name"],
                        "guarantee": mutant["guarantee"],
                        "detector_test": detector_test,
                        "status": "error",
                        "reason": "detector_timeout",
                        "detail": str(exc),
                    }
                else:
                    try:
                        detector_payload = _parse_detector_payload(completed)
                    except Exception as exc:
                        outcome = {
                            "id": mutant_id,
                            "name": mutant["name"],
                            "guarantee": mutant["guarantee"],
                            "detector_test": detector_test,
                            "status": "error",
                            "reason": "detector_protocol_error",
                            "detail": f"{type(exc).__name__}: {exc}",
                            "returncode": completed.returncode,
                            "stdout_tail": _tail(completed.stdout),
                            "stderr_tail": _tail(completed.stderr),
                        }
                    else:
                        if not _detector_bound_to_target(detector_payload, target=target):
                            status, reason = "error", "detector_not_bound_to_mutated_target"
                        else:
                            status, reason = _classify_detector_payload(
                                detector_payload,
                                detector_test=detector_test,
                            )
                        outcome = {
                            "id": mutant_id,
                            "name": mutant["name"],
                            "guarantee": mutant["guarantee"],
                            "detector_test": detector_test,
                            "status": status,
                            "reason": reason,
                            "returncode": completed.returncode,
                            "detector_result": detector_payload,
                            "stdout_tail": _tail(completed.stdout),
                            "stderr_tail": _tail(completed.stderr),
                        }
        except Exception as exc:  # fail closed: harness/config errors are not mutant kills
            outcome = {
                "id": mutant_id,
                "name": mutant.get("name"),
                "guarantee": mutant.get("guarantee"),
                "detector_test": detector_test,
                "status": "error",
                "reason": "mutation_harness_error",
                "detail": f"{type(exc).__name__}: {exc}",
            }
        finally:
            temp.cleanup()

        outcome["duration_seconds"] = round(time.monotonic() - started, 3)
        report["mutants"].append(outcome)
        print(
            f"MUTANT={mutant_id} STATUS={outcome['status'].upper()} "
            f"DETECTOR={detector_test} REASON={outcome.get('reason')}"
        )

    killed = sum(item["status"] == "killed" for item in report["mutants"])
    survived = sum(item["status"] == "survived" for item in report["mutants"])
    errors = sum(item["status"] == "error" for item in report["mutants"])
    total = len(report["mutants"])
    coverage = killed / total if total else 0.0
    report["summary"] = {
        "total": total,
        "killed": killed,
        "survived": survived,
        "errors": errors,
        "verification_guarantee_coverage": coverage,
        "kill_semantics": "named_detector_assertion_failure_only",
        "mutated_source_binding_required": True,
    }

    print(f"CAP_M0_MUTANTS_TOTAL={total}")
    print(f"CAP_M0_MUTANTS_KILLED={killed}")
    print(f"CAP_M0_MUTANTS_SURVIVED={survived}")
    print(f"CAP_M0_MUTANTS_ERRORS={errors}")
    print("CAP_M0_KILL_SEMANTICS=NAMED_DETECTOR_ASSERTION_FAILURE_ONLY")
    print("CAP_M0_MUTATED_SOURCE_BINDING=REQUIRED")
    print(f"VERIFICATION_GUARANTEE_COVERAGE={coverage:.3f}")

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return 0 if killed == total and survived == 0 and errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
