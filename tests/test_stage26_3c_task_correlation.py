from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "runtime" / "control_plane" / "cli.py"
PROCEDURE = "verified_workspace_artifact_v1"
ADMISSION = "stage26-3a-qualification"


class Stage263CTaskCorrelationTests(unittest.TestCase):
    def child_env(
        self,
        *,
        workspace: Path,
        state: Path,
        assigned_task_id: str | None = None,
    ) -> dict[str, str]:
        env = os.environ.copy()
        env["CHAT_LOCAL_FILES_ROOT"] = str(workspace)
        env["CHAT_PROCEDURE_STATE_ROOT"] = str(state)
        env["CHAT_PROCEDURE_ALLOW_CANDIDATE"] = ADMISSION
        if assigned_task_id is None:
            env.pop("CHAT_PROCEDURE_ASSIGNED_TASK_ID", None)
        else:
            env["CHAT_PROCEDURE_ASSIGNED_TASK_ID"] = assigned_task_id
        return env

    def invoke_cli(
        self,
        *,
        workspace: Path,
        state: Path,
        request: dict,
        assigned_task_id: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        completed = subprocess.run(
            [sys.executable, str(CLI)],
            cwd=ROOT,
            env=self.child_env(
                workspace=workspace,
                state=state,
                assigned_task_id=assigned_task_id,
            ),
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        payload = json.loads(completed.stdout)
        return completed, payload

    def request(self, name: str, content: str, *, resume_task_id: str | None = None) -> dict:
        request = {
            "procedure": PROCEDURE,
            "artifact_name": name,
            "content": content,
        }
        if resume_task_id is not None:
            request["resume_task_id"] = resume_task_id
        return request

    def test_parent_assigned_task_id_becomes_durable_procedure_identity(self) -> None:
        assigned = "0123456789abcdef0123456789abcdef"
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            completed, payload = self.invoke_cli(
                workspace=workspace,
                state=state,
                request=self.request("assigned-id.txt", "ASSIGNED_ID_OK"),
                assigned_task_id=assigned,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(payload["status"], "completed")
            self.assertEqual(payload["task_id"], assigned)
            self.assertEqual(payload["action_count"], 3)
            checkpoint_path = state / f"{assigned}.json"
            self.assertTrue(checkpoint_path.is_file())
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual(checkpoint["task_id"], assigned)
            self.assertEqual(checkpoint["status"], "completed")

    def test_preknown_assigned_id_survives_hard_child_crash_and_resumes_without_discovery(self) -> None:
        assigned = "abcdefabcdefabcdefabcdefabcdefab"
        request = self.request("assigned-crash.txt", "ASSIGNED_CRASH")
        crash_script = textwrap.dedent(
            """
            import os
            from runtime.control_plane import verified_workspace_artifact as wa

            def crash_after_stage(path, data):
                with path.open("xb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os._exit(81)

            wa._exclusive_create_file = crash_after_stage
            from runtime.control_plane import cli
            raise SystemExit(cli.main())
            """
        )

        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            crashed = subprocess.run(
                [sys.executable, "-c", crash_script],
                cwd=ROOT,
                env=self.child_env(
                    workspace=workspace,
                    state=state,
                    assigned_task_id=assigned,
                ),
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            self.assertEqual(crashed.returncode, 81, crashed.stderr)
            self.assertEqual(crashed.stdout, "")

            # The test already knows the parent-assigned correlation id. It does
            # not enumerate the private state directory to discover a task id.
            checkpoint_path = state / f"{assigned}.json"
            self.assertTrue(checkpoint_path.is_file())
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual(checkpoint["task_id"], assigned)
            self.assertEqual(checkpoint["prepared_intent"]["transition_id"], "stage_create")

            resumed, payload = self.invoke_cli(
                workspace=workspace,
                state=state,
                request=self.request(
                    "assigned-crash.txt",
                    "ASSIGNED_CRASH",
                    resume_task_id=assigned,
                ),
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(payload["status"], "completed")
            self.assertEqual(payload["task_id"], assigned)
            self.assertEqual(payload["resumed"], True)
            self.assertEqual(payload["action_count"], 3)

    def test_assigned_task_id_cannot_replace_existing_durable_task(self) -> None:
        assigned = "11111111111111111111111111111111"
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            first, first_payload = self.invoke_cli(
                workspace=workspace,
                state=state,
                request=self.request("first.txt", "FIRST"),
                assigned_task_id=assigned,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first_payload["task_id"], assigned)
            checkpoint_before = (state / f"{assigned}.json").read_bytes()

            second, second_payload = self.invoke_cli(
                workspace=workspace,
                state=state,
                request=self.request("second.txt", "SECOND"),
                assigned_task_id=assigned,
            )
            self.assertEqual(second.returncode, 2)
            self.assertEqual(second_payload["status"], "error")
            self.assertIn("assigned task id already has durable procedure state", second_payload["reason"])
            self.assertEqual((state / f"{assigned}.json").read_bytes(), checkpoint_before)
            self.assertFalse(
                (workspace / ".chat-agent-platform" / "stage26-3a" / "second.txt").exists()
            )

    def test_assigned_task_id_collision_is_rechecked_after_task_lock_acquisition(self) -> None:
        assigned = "33333333333333333333333333333333"
        sentinel = '{"owner":"first-run-prepared"}\n'
        race_script = textwrap.dedent(
            f"""
            from runtime.control_plane import verified_workspace_artifact as wa

            original_acquire = wa._acquire_task_lock
            sentinel = {sentinel!r}

            def acquire_then_publish_owner(state_root, task_id):
                task_lock = original_acquire(state_root, task_id)
                (state_root / f"{{task_id}}.json").write_text(sentinel, encoding="utf-8")
                return task_lock

            wa._acquire_task_lock = acquire_then_publish_owner
            from runtime.control_plane import cli
            raise SystemExit(cli.main())
            """
        )

        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            completed = subprocess.run(
                [sys.executable, "-c", race_script],
                cwd=ROOT,
                env=self.child_env(
                    workspace=workspace,
                    state=state,
                    assigned_task_id=assigned,
                ),
                input=json.dumps(self.request("collision-race.txt", "MUST_NOT_MUTATE")),
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            payload = json.loads(completed.stdout)

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(payload["status"], "error")
            self.assertIn("assigned task id already has durable procedure state", payload["reason"])
            self.assertEqual((state / f"{assigned}.json").read_text(encoding="utf-8"), sentinel)
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            self.assertFalse((reserved / "collision-race.txt").exists())
            self.assertEqual(list(reserved.glob(f".collision-race.txt.{assigned}.staging")), []) if reserved.exists() else None

    def test_assigned_task_id_is_rejected_on_public_resume(self) -> None:
        assigned = "22222222222222222222222222222222"
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            completed, payload = self.invoke_cli(
                workspace=Path(workspace_dir),
                state=Path(state_dir),
                request=self.request("resume-conflict.txt", "CONFLICT", resume_task_id=assigned),
                assigned_task_id=assigned,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(payload["status"], "error")
            self.assertIn("assigned task id is only valid for a new procedure run", payload["reason"])
            self.assertEqual(list(Path(state_dir).glob("*.json")), [])

    def test_malformed_assigned_task_id_fails_before_effect(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            completed, payload = self.invoke_cli(
                workspace=workspace,
                state=state,
                request=self.request("malformed.txt", "NO_EFFECT"),
                assigned_task_id="not-a-task-id",
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(payload["status"], "error")
            self.assertIn("assigned task id must be a 32-character lowercase hex task id", payload["reason"])
            self.assertEqual(list(state.glob("*.json")), [])
            self.assertFalse(
                (workspace / ".chat-agent-platform" / "stage26-3a" / "malformed.txt").exists()
            )


if __name__ == "__main__":
    unittest.main()
