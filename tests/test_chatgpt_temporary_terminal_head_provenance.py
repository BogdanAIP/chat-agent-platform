from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
import unittest

from runtime.agent_sessions import chatgpt_temporary, source_attestation
from runtime.agent_sessions.chatgpt_temporary_controller import TemporaryControllerState
from runtime.control_plane import delegation_state


TASK = "Return a bounded read-only answer."
TASK_SHA = hashlib.sha256(TASK.encode("utf-8")).hexdigest()
EXECUTION_GENERATION = "9" * 64
ASSETS = {
    "manifest.json": "1" * 64,
    "execution_generation.js": "5" * 64,
    "policy.js": "2" * 64,
    "background.js": "3" * 64,
    "content.js": "4" * 64,
}


def identity() -> dict[str, str]:
    return {
        "parent_task_id": "same-caller-parent",
        "subgoal_id": "same-subgoal",
        "worker_kind": "researcher",
        "worker_profile": delegation_state.WORKER_PROFILE,
        "task_sha256": TASK_SHA,
        "result_contract_id": "research-result-v1",
    }


def expected(head: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "adapter_id": source_attestation.ADAPTER_ID,
        "expected_head": head,
        "execution_generation": EXECUTION_GENERATION,
        "assets": dict(ASSETS),
    }


def report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "adapter_id": source_attestation.ADAPTER_ID,
        "execution_generation": EXECUTION_GENERATION,
        "assets": dict(ASSETS),
    }


def child_evidence(state: TemporaryControllerState) -> dict[str, object]:
    return {
        "schema_version": 1,
        "adapter_id": chatgpt_temporary.ADAPTER_ID,
        "run_id": state.launch.run_id,
        "temporary_mode": True,
        "fresh_context": True,
        "personalization_disabled": True,
        "plugin_markers": [],
        "session_id": "chrome-tab:17",
        "conversation_id": None,
        "observation_ref": "chatgpt-temporary:chrome-tab:17:pre-send:1",
    }


def authority_request(state: TemporaryControllerState) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": state.launch.run_id,
        "delegation_id": state.launch.delegation_id,
        "delivery_id": state.launch.delivery_id,
        "browser_claim_committed": True,
        "browser_claim_id": state.launch.delivery_id,
        "child_evidence": child_evidence(state),
        "runtime_attestation": report(),
    }


def result_text(state: TemporaryControllerState) -> str:
    raw = {
        "schema_version": 1,
        "delegation_id": state.launch.delegation_id,
        "delivery_id": state.launch.delivery_id,
        "worker_kind": "researcher",
        "result_contract_id": "research-result-v1",
        "status": "COMPLETED",
        "payload": "bounded result",
    }
    return (
        chatgpt_temporary.RAW_RESULT_BEGIN
        + "\n"
        + json.dumps(raw, separators=(",", ":"))
        + "\n"
        + chatgpt_temporary.RAW_RESULT_END
    )


class TerminalHeadProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.state_root = root / "state"
        self.output_root = root / "output"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def controller(self, head: str, suffix: str) -> TemporaryControllerState:
        return TemporaryControllerState(
            identity_value=identity(),
            task=TASK,
            expected_runtime_attestation_value=expected(head),
            state_root=self.state_root,
            output_dir=self.output_root / suffix,
        )

    def deliver_without_result(self, state: TemporaryControllerState) -> None:
        state.authorize_send(authority_request(state))
        state.record_delivery(
            {
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "task_sha256": TASK_SHA,
                "outcome": "delivered",
                "evidence_ref": "chatgpt-temporary:delivery:visible:1",
            }
        )

    def record_terminal_result(self, state: TemporaryControllerState) -> None:
        self.deliver_without_result(state)
        state.record_capture(
            {
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "result_text": result_text(state),
                "runtime_attestation": report(),
            }
        )

    def test_same_head_terminal_readback_succeeds(self) -> None:
        head = "a" * 40
        first = self.controller(head, "first")
        self.record_terminal_result(first)
        restarted = self.controller(head, "same-head")
        self.assertFalse(restarted.launch.launch_now)
        self.assertTrue(restarted.done.is_set())
        self.assertTrue((self.output_root / "same-head" / "result.json").is_file())

    def test_different_head_cannot_reproject_old_terminal_result(self) -> None:
        first = self.controller("a" * 40, "first")
        self.record_terminal_result(first)
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError,
            "bound worker runtime provenance",
        ):
            self.controller("b" * 40, "different-head")
        self.assertFalse((self.output_root / "different-head" / "result.json").exists())

    def test_different_head_rejects_delivered_open_worker_before_capture_or_timeout(self) -> None:
        first = self.controller("a" * 40, "first")
        self.deliver_without_result(first)
        before = delegation_state.load_delegation(identity(), state_root=self.state_root)
        self.assertEqual("delivered", before.delivery_state)
        self.assertEqual("open", before.result_state)

        with self.assertRaisesRegex(
            delegation_state.DelegationStateError,
            "bound worker runtime provenance",
        ):
            self.controller("b" * 40, "different-head-open")

        after = delegation_state.load_delegation(identity(), state_root=self.state_root)
        self.assertEqual("delivered", after.delivery_state)
        self.assertEqual("open", after.result_state)
        self.assertIsNone(after.result_status)
        self.assertFalse((self.output_root / "different-head-open" / "result.json").exists())


if __name__ == "__main__":
    unittest.main()
