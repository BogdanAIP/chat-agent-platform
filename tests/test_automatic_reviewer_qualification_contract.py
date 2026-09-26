from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from runtime.control_plane import delegation_state
from runtime.control_plane import independent_review_state as review_state
from runtime.control_plane.independent_review_delegation import prepare_review_delegation
from runtime.control_plane.independent_review_procedures import _submit_delegated_result_via_registered_procedure


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts" / "automatic-reviewer-qualification.py"
HARNESS = ROOT / "scripts" / "qualify-automatic-reviewer.ps1"


BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40


def _identity_value() -> dict[str, object]:
    return {
        "repository": "BogdanAIP/chat-agent-platform",
        "pr_number": 159,
        "base_sha": BASE_SHA,
        "head_sha": HEAD_SHA,
        "review_skill": "code-review",
        "review_skill_version": "1.1",
    }


def _pass_result(review_run_id: str) -> str:
    return "\n".join(
        [
            "REVIEW_RESULT_V1",
            "repository=BogdanAIP/chat-agent-platform",
            "pr_number=159",
            f"base_sha={BASE_SHA}",
            f"head_sha={HEAD_SHA}",
            f"review_policy_ref={BASE_SHA}",
            "review_skill=code-review",
            "review_skill_version=1.1",
            "review_context=ordinary_chat_fresh",
            "status=PASS",
            "review_validity=CURRENT",
            "reported_findings=0",
            "rejected_candidates=0",
            "reviewed_at=2026-09-18T12:00:00+00:00",
            f"review_run_id={review_run_id}",
        ]
    )


class AutomaticReviewerQualificationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = DRIVER.read_text(encoding="utf-8")
        self.harness = HARNESS.read_text(encoding="utf-8")

    def test_driver_parses_and_reuses_review_and_delegation_contracts(self) -> None:
        ast.parse(self.driver)
        self.assertIn("prepare_review_operation", self.driver)
        self.assertIn("mark_dispatch_attempted", self.driver)
        self.assertIn("review_delegation_identity", self.driver)
        self.assertIn("_settle_delegated_result", self.driver)
        self.assertIn("reconcile_independent_review_result", self.driver)

    def test_driver_runs_directly_from_scripts_directory(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(DRIVER), "--help"],
            cwd=DRIVER.parent,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout={completed.stdout}\nstderr={completed.stderr}",
        )
        self.assertNotIn("ModuleNotFoundError", completed.stderr)

    def test_prepare_rejects_capability_artifacts_outside_private_manager_state(self) -> None:
        with tempfile.TemporaryDirectory() as local_dir:
            local_root = Path(local_dir)
            private_root = (
                local_root
                / "ChatAgentPlatform"
                / "state"
                / "automatic-reviewer-qualification"
                / "test"
            )
            reviewer_state_root = private_root / "review-state"
            unsafe_output_dir = (
                local_root
                / "ChatAgentPlatform"
                / "automatic-reviewer"
                / "qualification"
                / "leaked-adapter"
            )
            reviewer_state_root.mkdir(parents=True, exist_ok=True)

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_root)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(DRIVER),
                    "prepare",
                    "--repository",
                    "BogdanAIP/chat-agent-platform",
                    "--pr-number",
                    "159",
                    "--base-sha",
                    BASE_SHA,
                    "--head-sha",
                    HEAD_SHA,
                    "--review-skill",
                    "code-review",
                    "--review-skill-version",
                    "1.1",
                    "--reviewer-state-root",
                    str(reviewer_state_root),
                    "--output-dir",
                    str(unsafe_output_dir),
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            self.assertEqual(2, completed.returncode)
            self.assertEqual(
                {"status": "error", "reason": "ReviewStateError"},
                json.loads(completed.stdout),
            )
            self.assertFalse((unsafe_output_dir / "review-task.txt").exists())
            self.assertFalse(
                (reviewer_state_root / review_state.STATE_DIRECTORY).exists(),
                "path validation must happen before private reviewer genesis is created",
            )

    def test_prepare_keeps_task_capability_under_private_manager_state(self) -> None:
        with tempfile.TemporaryDirectory() as local_dir:
            local_root = Path(local_dir)
            private_root = (
                local_root
                / "ChatAgentPlatform"
                / "state"
                / "automatic-reviewer-qualification"
                / "test"
            )
            reviewer_state_root = private_root / "review-state"
            output_dir = private_root / "adapter"

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_root)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(DRIVER),
                    "prepare",
                    "--repository",
                    "BogdanAIP/chat-agent-platform",
                    "--pr-number",
                    "159",
                    "--base-sha",
                    BASE_SHA,
                    "--head-sha",
                    HEAD_SHA,
                    "--review-skill",
                    "code-review",
                    "--review-skill-version",
                    "1.1",
                    "--reviewer-state-root",
                    str(reviewer_state_root),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            self.assertEqual(
                0,
                completed.returncode,
                msg=f"stdout={completed.stdout}\nstderr={completed.stderr}",
            )
            result = json.loads(completed.stdout)
            task_path = Path(result["task_file"]).resolve()
            manager_state_root = (
                local_root / "ChatAgentPlatform" / "state"
            ).resolve()
            self.assertTrue(task_path.is_relative_to(manager_state_root))
            self.assertTrue(task_path.is_relative_to(private_root.resolve()))
            self.assertIn(
                "review_run_id=",
                task_path.read_text(encoding="utf-8"),
                "the capability-bearing task must remain protected by manager-state placement",
            )

    def test_settle_reads_canonical_submission_and_opaque_generic_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as local_dir:
            local_root = Path(local_dir)
            reviewer_state_root = (
                local_root
                / "ChatAgentPlatform"
                / "state"
                / "automatic-reviewer-qualification"
                / "test"
                / "review-state"
            )
            delegation_root = (
                local_root
                / "ChatAgentPlatform"
                / "agent-sessions"
                / "private-state"
            )
            reviewer_state_root.mkdir(parents=True, exist_ok=True)
            delegation_root.mkdir(parents=True, exist_ok=True)

            prepared_review = review_state.prepare_review_operation(
                _identity_value(),
                state_root=reviewer_state_root,
            )
            review_state.mark_dispatch_attempted(
                _identity_value(),
                state_root=reviewer_state_root,
            )
            _task, delegated_identity = prepare_review_delegation(
                prepared_review.identity,
                review_run_id=prepared_review.review_run_id,
                delegation_state_root=delegation_root,
            )
            prepared = delegation_state.prepare_delegation(
                delegated_identity,
                state_root=delegation_root,
            )
            delegation_state.mark_launch_attempted(
                delegated_identity,
                run_id=prepared.run_id,
                state_root=delegation_root,
            )
            delegation_state.bind_worker_session(
                delegated_identity,
                run_id=prepared.run_id,
                session_ref_value={
                    "adapter_id": "chatgpt-temporary",
                    "session_id": "qualification-settle-test",
                    "conversation_id": None,
                    "ownership": "manager_owned",
                    "observation_ref": "qualification-test",
                },
                state_root=delegation_root,
            )
            delegation_state.claim_delivery(
                delegated_identity,
                run_id=prepared.run_id,
                state_root=delegation_root,
            )
            delegation_state.record_delivery_outcome(
                delegated_identity,
                run_id=prepared.run_id,
                outcome="delivered",
                evidence_ref="qualification-delivered",
                state_root=delegation_root,
            )
            payload = _pass_result(prepared_review.review_run_id)
            _submit_delegated_result_via_registered_procedure(
                prepared_review.review_run_id,
                payload,
                state_root=reviewer_state_root,
            )
            receipt = delegation_state.REVIEW_SUBMITTED_RECEIPT
            delegation_state.record_worker_result(
                delegated_identity,
                run_id=prepared.run_id,
                result_value={
                    "schema_version": 1,
                    "delegation_id": prepared.delegation_id,
                    "delivery_id": prepared.delivery_id,
                    "worker_kind": delegated_identity["worker_kind"],
                    "result_contract_id": delegated_identity["result_contract_id"],
                    "status": "COMPLETED",
                    "payload": receipt,
                    "payload_sha256": hashlib.sha256(receipt.encode("utf-8")).hexdigest(),
                },
                state_root=delegation_root,
            )

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_root)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(DRIVER),
                    "settle",
                    "--repository",
                    "BogdanAIP/chat-agent-platform",
                    "--pr-number",
                    "159",
                    "--base-sha",
                    BASE_SHA,
                    "--head-sha",
                    HEAD_SHA,
                    "--review-skill",
                    "code-review",
                    "--review-skill-version",
                    "1.1",
                    "--reviewer-state-root",
                    str(reviewer_state_root),
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            self.assertEqual(
                0,
                completed.returncode,
                msg=f"stdout={completed.stdout}\nstderr={completed.stderr}",
            )
            result = json.loads(completed.stdout)
            self.assertEqual("automatic-result-recorded", result["result_state"])
            self.assertEqual("automatic", result["result_source"])
            self.assertEqual(payload, result["result"])
            generic = delegation_state.load_delegation(delegated_identity, state_root=delegation_root)
            self.assertEqual(receipt, generic.result_payload)
            self.assertNotIn("REVIEW_RESULT_V1", json.dumps(generic.__dict__, default=str))

    def test_harness_reuses_exact_head_generic_temporary_launcher(self) -> None:
        self.assertIn("launch-chatgpt-temporary-worker.ps1", self.harness)
        self.assertIn("-ExpectedHead", self.harness)
        self.assertIn("-WorkerKind", self.harness)
        self.assertIn("-ResultContractId", self.harness)
        self.assertIn("code-review", self.harness)
        self.assertIn("review_result_v1", self.harness)
        self.assertIn("fresh_readonly_worker_v1", self.harness)

    def test_harness_requires_clean_exact_head_before_review_task_creation(self) -> None:
        head_check = self.harness.index("EXACT_HEAD_MISMATCH")
        dirty_check = self.harness.index("Qualification source must be clean")
        prepare = self.harness.index("$prepareRaw =")
        self.assertLess(head_check, prepare)
        self.assertLess(dirty_check, prepare)

    def test_harness_never_adds_manual_send_or_result_copy_path(self) -> None:
        self.assertIn("CAP_REVIEW_MANUAL_SEND_REQUIRED=False", self.harness)
        self.assertIn("CAP_AUTOMATIC_REVIEWER_QUALIFICATION=PASS", self.harness)
        self.assertNotIn("Read-Host", self.harness)
        self.assertNotIn("Set-Clipboard", self.harness)
        self.assertNotIn("Get-Clipboard", self.harness)

    def test_qualification_state_is_private_and_generic_state_remains_accepted_owner(self) -> None:
        self.assertIn(
            "ChatAgentPlatform\\state\\automatic-reviewer-qualification",
            self.harness,
        )
        self.assertNotIn(
            "ChatAgentPlatform\\automatic-reviewer\\qualification",
            self.harness,
        )
        self.assertIn("_require_private_qualification_path", self.driver)
        self.assertIn("review_delegation_state_root", self.driver)
        self.assertNotIn("procedure-runtime", self.driver)


if __name__ == "__main__":
    unittest.main()
