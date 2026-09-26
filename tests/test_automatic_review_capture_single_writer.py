from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.agent_sessions import chatgpt_temporary, source_attestation
from runtime.agent_sessions.chatgpt_temporary_controller import TemporaryControllerState
from runtime.control_plane import delegation_state, independent_review_state as reviewer_state
from runtime.control_plane.independent_review_delegation import (
    bind_review_capture,
    prepare_review_delegation,
    settle_review_from_delegation,
)
from runtime.control_plane.independent_review_procedures import (
    _submit_delegated_result_via_registered_procedure,
)


IDENTITY = {
    "repository": "BogdanAIP/chat-agent-platform",
    "pr_number": 159,
    "base_sha": "1" * 40,
    "head_sha": "2" * 40,
    "review_skill": "code-review",
    "review_skill_version": "1.1",
}
ASSETS = {name: f"{index + 1:x}".rjust(64, "0") for index, name in enumerate(source_attestation.RUNTIME_ASSETS)}
ATTESTATION = {
    "schema_version": 1,
    "adapter_id": source_attestation.ADAPTER_ID,
    "expected_head": "2" * 40,
    "execution_generation": "9" * 64,
    "assets": ASSETS,
}


def review_result(run_id: str) -> str:
    return "\n".join((
        "REVIEW_RESULT_V1",
        "repository=BogdanAIP/chat-agent-platform",
        "pr_number=159",
        f"base_sha={IDENTITY['base_sha']}",
        f"head_sha={IDENTITY['head_sha']}",
        f"review_policy_ref={IDENTITY['base_sha']}",
        "review_skill=code-review",
        "review_skill_version=1.1",
        "review_context=ordinary_chat_fresh",
        "status=PASS",
        "review_validity=CURRENT",
        "reported_findings=0",
        "rejected_candidates=0",
        "reviewed_at=2026-09-26T12:00:00+00:00",
        f"review_run_id={run_id}",
    ))


class AutomaticReviewCaptureSingleWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.reviewer_root = root / "reviewer-state"
        self.delegation_root = root / "agent-sessions"
        self.output = root / "output"
        self.prepared = reviewer_state.prepare_review_operation(IDENTITY, state_root=self.reviewer_root)
        reviewer_state.mark_dispatch_attempted(IDENTITY, state_root=self.reviewer_root)
        self.task, self.delegation_identity = prepare_review_delegation(
            self.prepared.identity,
            review_run_id=self.prepared.review_run_id,
            delegation_state_root=self.delegation_root,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def controller(self, submit=None) -> TemporaryControllerState:
        if submit is None:
            submit = lambda nonce, payload: _submit_delegated_result_via_registered_procedure(
                nonce, payload, state_root=self.reviewer_root
            )
        capture = bind_review_capture(
            self.delegation_identity,
            task=self.task,
            reviewer_identity_value=IDENTITY,
            reviewer_state_root=self.reviewer_root,
            delegation_state_root=self.delegation_root,
            submit_result=submit,
        )
        state = TemporaryControllerState(
            identity_value=self.delegation_identity,
            task=self.task,
            launch_handle="7" * 64,
            expected_runtime_attestation_value=ATTESTATION,
            state_root=self.delegation_root,
            output_dir=self.output,
            result_capture=capture,
        )
        runtime_report = {key: value for key, value in ATTESTATION.items() if key != "expected_head"}
        state.authorize_send({
            "schema_version": 1,
            "run_id": state.launch.run_id,
            "delegation_id": state.launch.delegation_id,
            "delivery_id": state.launch.delivery_id,
            "expected_runtime_head": ATTESTATION["expected_head"],
            "prompt_sha256": state.launch.prompt_sha256,
            "browser_claim_committed": True,
            "browser_claim_id": state.launch.delivery_id,
            "child_evidence": {
                "schema_version": 1,
                "adapter_id": chatgpt_temporary.ADAPTER_ID,
                "run_id": state.launch.run_id,
                "temporary_mode": True,
                "fresh_context": True,
                "personalization_disabled": True,
                "plugin_markers": [],
                "session_id": "chrome-tab:review",
                "conversation_id": None,
                "observation_ref": "chatgpt-temporary:review:pre-send:1",
            },
            "runtime_attestation": runtime_report,
        })
        state.record_delivery({
            "schema_version": 1,
            "run_id": state.launch.run_id,
            "delegation_id": state.launch.delegation_id,
            "delivery_id": state.launch.delivery_id,
            "task_sha256": self.delegation_identity["task_sha256"],
            "outcome": "delivered",
            "evidence_ref": "chatgpt-temporary:review:delivered:1",
        })
        cleanup = state.record_event({
            "schema_version": 1,
            "run_id": state.launch.run_id,
            "delegation_id": state.launch.delegation_id,
            "delivery_id": state.launch.delivery_id,
            "event": "delivery-visible",
            "details": {
                "post_delivery_ui_disarmed": True,
                "launch_url_clean": True,
                "composer_clean": True,
            },
        })["cleanup_token"]
        self.capture_request = {
            "schema_version": 1,
            "run_id": state.launch.run_id,
            "delegation_id": state.launch.delegation_id,
            "delivery_id": state.launch.delivery_id,
            "cleanup_token": cleanup,
            "capture_token": state.prepare_capture({
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "cleanup_token": cleanup,
                "runtime_attestation": runtime_report,
            })["capture_token"],
        }
        return state

    def capture(self, state: TemporaryControllerState, payload: str, status: str = "COMPLETED") -> dict:
        result = {
            "schema_version": 1,
            "delegation_id": state.launch.delegation_id,
            "delivery_id": state.launch.delivery_id,
            "worker_kind": "code-review",
            "result_contract_id": "review_result_v1",
            "status": status,
            "payload": payload,
        }
        raw = f"{chatgpt_temporary.RAW_RESULT_BEGIN}\n{json.dumps(result)}\n{chatgpt_temporary.RAW_RESULT_END}"
        return state.record_capture({**self.capture_request, "result_text": raw})

    def generic(self):
        return delegation_state.load_delegation(self.delegation_identity, state_root=self.delegation_root)

    def canonical(self):
        return reviewer_state.reconcile_independent_review_result(IDENTITY, state_root=self.reviewer_root)

    def test_registered_submit_commits_before_any_generic_result_and_only_receipt_persists(self) -> None:
        def registered_submit(nonce, payload):
            self.assertEqual("open", self.generic().result_state)
            self.assertFalse((self.output / "result.json").exists())
            return _submit_delegated_result_via_registered_procedure(
                nonce, payload, state_root=self.reviewer_root
            )

        state = self.controller(submit=registered_submit)
        payload = review_result(self.prepared.review_run_id)
        response = self.capture(state, payload)
        self.assertEqual("COMPLETED", response["worker_status"])
        self.assertEqual(payload, self.canonical()["result"])
        self.assertEqual(delegation_state.REVIEW_SUBMITTED_RECEIPT, self.generic().result_payload)
        self.assertEqual(delegation_state.REVIEW_SUBMITTED_RECEIPT,
                         json.loads((self.output / "result.json").read_text())["payload"])
        self.assertNotIn(payload, (self.output / "result.json").read_text())
        self.assertEqual("already_recorded", settle_review_from_delegation(
            IDENTITY, reviewer_state_root=self.reviewer_root,
            delegation_state_root=self.delegation_root,
        )["status"])

    def test_failed_submit_never_records_review_in_generic_store_or_projection(self) -> None:
        def denied(_nonce, _payload):
            raise reviewer_state.ReviewStateError("registered submission unavailable")

        state = self.controller(submit=denied)
        with self.assertRaises(reviewer_state.ReviewStateError):
            self.capture(state, review_result(self.prepared.review_run_id))
        self.assertEqual("open", self.generic().result_state)
        self.assertEqual("open", self.canonical()["result_state"])
        self.assertFalse((self.output / "result.json").exists())

    def test_after_commit_checkpoint_failure_recovers_from_canonical_result(self) -> None:
        state = self.controller()
        payload = review_result(self.prepared.review_run_id)
        with patch("runtime.agent_sessions.chatgpt_temporary.record_temporary_worker_result", side_effect=OSError("checkpoint fail")):
            with self.assertRaises(OSError):
                self.capture(state, payload)
        self.assertEqual("automatic-result-recorded", self.canonical()["result_state"])
        self.assertEqual("open", self.generic().result_state)
        self.assertFalse((self.output / "result.json").exists())
        self.assertEqual("already_recorded", settle_review_from_delegation(
            IDENTITY, reviewer_state_root=self.reviewer_root,
            delegation_state_root=self.delegation_root,
        )["status"])

    def test_after_commit_projection_failure_keeps_only_opaque_generic_receipt(self) -> None:
        state = self.controller()
        payload = review_result(self.prepared.review_run_id)
        with patch.object(state, "_write_snapshot_result", side_effect=OSError("projection fail")):
            with self.assertRaises(OSError):
                self.capture(state, payload)
        self.assertEqual(payload, self.canonical()["result"])
        self.assertEqual(delegation_state.REVIEW_SUBMITTED_RECEIPT, self.generic().result_payload)
        self.assertFalse((self.output / "result.json").exists())
        self.assertEqual("already_recorded", settle_review_from_delegation(
            IDENTITY, reviewer_state_root=self.reviewer_root,
            delegation_state_root=self.delegation_root,
        )["status"])

    def test_manual_fallback_wins_before_late_capture(self) -> None:
        state = self.controller()
        reviewer_state.reconcile_independent_review_result(
            {**IDENTITY, "manual_result": review_result(self.prepared.review_run_id).replace(
                f"\nreview_run_id={self.prepared.review_run_id}", ""
            )}, state_root=self.reviewer_root,
        )
        with self.assertRaises(reviewer_state.ReviewStateError):
            self.capture(state, review_result(self.prepared.review_run_id))
        self.assertEqual("manual-fallback-recorded", self.canonical()["result_state"])
        self.assertEqual("open", self.generic().result_state)

    def test_noncompleting_capture_persists_only_constant_marker(self) -> None:
        state = self.controller()
        response = self.capture(state, "evidence unavailable", status="ABSTAIN")
        self.assertEqual("ABSTAIN", response["worker_status"])
        self.assertEqual(delegation_state.REVIEW_NONCOMPLETING_RECEIPT, self.generic().result_payload)
        self.assertEqual("open", self.canonical()["result_state"])

    def test_binding_refuses_different_task_before_browser_preflight(self) -> None:
        with self.assertRaises(reviewer_state.ReviewStateError):
            bind_review_capture(
                self.delegation_identity, task=self.task + " extra",
                reviewer_identity_value=IDENTITY, reviewer_state_root=self.reviewer_root,
                delegation_state_root=self.delegation_root,
                submit_result=lambda _nonce, _payload: self.fail("unexpected submit"),
            )
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
