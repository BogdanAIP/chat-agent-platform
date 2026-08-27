from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scripts" / "stage26-windows-case-desk-fixture.ps1"


@unittest.skipUnless(os.name == "nt", "WinForms fixture startup requires Windows")
class WindowsCaseDeskFixtureStartupTests(unittest.TestCase):
    def _seed(self, run_id: str) -> dict:
        return {
            "schema_version": 1,
            "run_id": run_id,
            "target_id": f"CASE-{run_id}-4821",
            "expected": {
                "status": "Approved",
                "note": f"Reviewed by ordinary Chat {run_id}",
            },
            "cases": [
                {
                    "id": f"CASE-{run_id}-4821",
                    "client": "Marina Volkova",
                    "status": "Pending",
                    "notes": [f"Imported record {run_id}-0"],
                },
                {
                    "id": f"CASE-{run_id}-4822",
                    "client": "Marina Volkova",
                    "status": "Approved",
                    "notes": [f"Imported record {run_id}-1"],
                },
                {
                    "id": f"CASE-{run_id}-4831",
                    "client": "Maria Volkova",
                    "status": "Pending",
                    "notes": [f"Imported record {run_id}-2"],
                },
                {
                    "id": f"CASE-{run_id}-4832",
                    "client": "Marina Volkov",
                    "status": "Needs Review",
                    "notes": [f"Imported record {run_id}-3"],
                },
            ],
        }

    def _run_fixture(self, *, exercise_event_state_regression: bool = False) -> tuple[str, dict]:
        run_id = "12AB34CD"
        seed = self._seed(run_id)

        with tempfile.TemporaryDirectory(prefix="stage26-win-case-fixture-") as tmp:
            root = Path(tmp)
            seed_path = root / "seed.json"
            state_path = root / "state.json"
            audit_path = root / "audit.jsonl"
            ready_path = root / "ready.txt"
            close_path = root / "close.txt"
            seed_path.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")

            cmd = [
                "pwsh.exe",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-STA",
                "-File",
                str(FIXTURE),
                "-SeedPath",
                str(seed_path),
                "-StatePath",
                str(state_path),
                "-AuditPath",
                str(audit_path),
                "-ReadyPath",
                str(ready_path),
                "-ClosePath",
                str(close_path),
                "-RunId",
                run_id,
            ]
            if exercise_event_state_regression:
                cmd.append("-ExerciseEventStateRegression")

            proc = subprocess.Popen(
                cmd,
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline and not ready_path.exists():
                    code = proc.poll()
                    if code is not None:
                        stdout, stderr = proc.communicate(timeout=2)
                        self.fail(
                            "Case Desk fixture exited before READY "
                            f"with code {code}.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                        )
                    time.sleep(0.1)

                self.assertTrue(ready_path.exists(), "Case Desk fixture did not create ready.txt")
                self.assertTrue(state_path.exists(), "Case Desk fixture did not create state.json")
                state = json.loads(state_path.read_text(encoding="utf-8-sig"))

                close_path.write_text("CLOSE\n", encoding="ascii")
                proc.wait(timeout=10)
                self.assertEqual(proc.returncode, 0)
                return run_id, state
            finally:
                if proc.poll() is None:
                    try:
                        close_path.write_text("CLOSE\n", encoding="ascii")
                    except OSError:
                        pass
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=3)

    def test_fixture_reaches_ready_and_clean_initial_state(self) -> None:
        run_id, state = self._run_fixture()
        self.assertEqual(state["schema_version"], 1)
        self.assertEqual(state["run_id"], run_id)
        self.assertEqual(state["save_count"], 0)
        self.assertIsNone(state["selected_case_id"])
        self.assertIsNone(state["draft_status"])
        self.assertEqual(len(state["cases"]), 4)

    def test_selection_persists_across_later_textchanged_event(self) -> None:
        run_id, state = self._run_fixture(exercise_event_state_regression=True)
        expected_case = f"CASE-{run_id}-4821"
        expected_note = f"EVENT_STATE_REGRESSION_{run_id}"
        expected_note_hash = hashlib.sha256(expected_note.encode("utf-8")).hexdigest()

        self.assertEqual(state["selected_case_id"], expected_case)
        self.assertIsNone(state["draft_status"])
        self.assertEqual(state["draft_note_sha256"], expected_note_hash)
        self.assertEqual(state["save_count"], 0)
        self.assertEqual(len(state["cases"]), 4)


if __name__ == "__main__":
    unittest.main()
