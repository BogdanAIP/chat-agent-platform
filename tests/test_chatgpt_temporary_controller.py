from __future__ import annotations

import hashlib
import json
import tempfile
import threading
from pathlib import Path
import unittest

from runtime.agent_sessions import chatgpt_temporary, source_attestation
from runtime.agent_sessions.chatgpt_temporary_controller import TemporaryControllerState
from runtime.control_plane import delegation_state


TASK = "Read the supplied bounded question and return a short research summary without changing external state."
TASK_SHA = hashlib.sha256(TASK.encode("utf-8")).hexdigest()
EXECUTION_GENERATION = "9" * 64
RUNTIME_ASSETS = {
    "manifest.json": "1" * 64,
    "execution_generation.js": "5" * 64,
    "policy.js": "2" * 64,
    "background.js": "3" * 64,
    "content.js": "4" * 64,
}


def identity_dict() -> dict[str, str]:
    return {
        "parent_task_id": "manager-task-controller-test",
        "subgoal_id": "temporary-worker-controller",
        "worker_kind": "researcher",
        "worker_profile": delegation_state.WORKER_PROFILE,
        "task_sha256": TASK_SHA,
        "result_contract_id": "research-result-v1",
    }


def expected_runtime_attestation() -> dict[str, object]:
    return {
        "schema_version": 1,
        "adapter_id": source_attestation.ADAPTER_ID,
        "expected_head": "a" * 40,
        "execution_generation": EXECUTION_GENERATION,
        "assets": dict(RUNTIME_ASSETS),
    }


def runtime_report(*, execution_generation: str = EXECUTION_GENERATION, **overrides: str) -> dict[str, object]:
    assets = dict(RUNTIME_ASSETS)
    assets.update(overrides)
    return {
        "schema_version": 1,
        "adapter_id": source_attestation.ADAPTER_ID,
        "execution_generation": execution_generation,
        "assets": assets,
    }


def child_evidence(state: TemporaryControllerState, *, session_id: str = "chrome-tab:5") -> dict[str, object]:
    return {
        "schema_version": 1,
        "adapter_id": chatgpt_temporary.ADAPTER_ID,
        "run_id": state.launch.run_id,
        "temporary_mode": True,
        "fresh_context": True,
        "personalization_disabled": True,
        "plugin_markers": [],
        "session_id": session_id,
        "conversation_id": None,
        "observation_ref": f"chatgpt-temporary:{session_id}:pre-send:1",
    }


def authority_request(
    state: TemporaryControllerState,
    *,
    evidence: dict[str, object] | None = None,
    attestation: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": state.launch.run_id,
        "delegation_id": state.launch.delegation_id,
        "delivery_id": state.launch.delivery_id,
        "browser_claim_committed": True,
        "browser_claim_id": state.launch.delivery_id,
        "child_evidence": evidence or child_evidence(state),
        "runtime_attestation": attestation or runtime_report(),
    }


def result_text(state: TemporaryControllerState, payload: str) -> str:
    return (
        chatgpt_temporary.RAW_RESULT_BEGIN
        + "\n"
        + json.dumps(
            {
                "schema_version": 1,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "worker_kind": "researcher",
                "result_contract_id": "research-result-v1",
                "status": "COMPLETED",
                "payload": payload,
            },
            separators=(",", ":"),
        )
        + "\n"
        + chatgpt_temporary.RAW_RESULT_END
    )


class TemporaryControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.state_root = root / "private-state"
        self.output_root = root / "output"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def controller(self, suffix: str = "first") -> TemporaryControllerState:
        return TemporaryControllerState(
            identity_value=identity_dict(),
            task=TASK,
            expected_runtime_attestation_value=expected_runtime_attestation(),
            state_root=self.state_root,
            output_dir=self.output_root / suffix,
        )

    def deliver(self, state: TemporaryControllerState) -> None:
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

    def test_controller_restart_recovers_same_private_capability_without_relaunch(self) -> None:
        first = self.controller("first")
        second = self.controller("second")
        self.assertTrue(first.launch.launch_now)
        self.assertFalse(second.launch.launch_now)
        self.assertEqual(first.launch.run_id, second.launch.run_id)
        self.assertEqual(first.token, second.token)
        self.assertEqual(first.launch.delivery_id, second.launch.delivery_id)
        launch = json.loads((self.output_root / "second" / "launch.json").read_text(encoding="utf-8"))
        self.assertFalse(launch["launch_now"])
        self.assertEqual("launch-attempted", launch["launch_state"])
        self.assertEqual("a" * 40, launch["expected_runtime_head"])
        self.assertEqual(EXECUTION_GENERATION, launch["execution_generation"])

    def test_browser_claim_must_be_committed_before_local_send_authority(self) -> None:
        state = self.controller()
        request = authority_request(state)
        request["browser_claim_committed"] = False
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "browser send claim"):
            state.authorize_send(request)
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("launch-attempted", snapshot.launch_state)
        self.assertEqual("prepared", snapshot.delivery_state)

    def test_runtime_attestation_mismatch_blocks_child_bind_and_send_claim(self) -> None:
        state = self.controller()
        wrong = runtime_report(**{"background.js": "f" * 64})
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "runtime attestation mismatch"):
            state.authorize_send(authority_request(state, attestation=wrong))
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("launch-attempted", snapshot.launch_state)
        self.assertEqual("prepared", snapshot.delivery_state)
        self.assertIsNone(snapshot.worker_session_ref)

    def test_stale_execution_generation_blocks_child_bind_even_when_resource_hashes_match(self) -> None:
        state = self.controller()
        wrong = runtime_report(execution_generation="8" * 64)
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "execution generation mismatch"):
            state.authorize_send(authority_request(state, attestation=wrong))
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("prepared", snapshot.delivery_state)
        self.assertIsNone(snapshot.worker_session_ref)

    def test_successful_send_authority_durably_binds_running_extension_attestation(self) -> None:
        state = self.controller()
        result = state.authorize_send(authority_request(state))
        self.assertTrue(result["send_authorized"])
        self.assertRegex(result["runtime_attestation_sha256"], r"^[0-9a-f]{64}$")
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertIn(
            f":runtime:{result['runtime_attestation_sha256']}",
            snapshot.worker_session_ref.observation_ref,
        )

    def test_concurrent_authority_requests_can_never_both_authorize_send(self) -> None:
        state = self.controller()
        barrier = threading.Barrier(3)
        outcomes: list[bool | str] = []
        mutex = threading.Lock()

        def contender() -> None:
            barrier.wait()
            try:
                result = state.authorize_send(authority_request(state))
                outcome: bool | str = bool(result["send_authorized"])
            except (delegation_state.DelegationStateError, BlockingIOError) as exc:
                outcome = type(exc).__name__
            with mutex:
                outcomes.append(outcome)

        threads = [threading.Thread(target=contender) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual(2, len(outcomes))
        self.assertEqual(1, sum(value is True for value in outcomes))
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("child-bound", snapshot.launch_state)
        self.assertEqual("claimed", snapshot.delivery_state)

    def test_foreign_second_tab_cannot_replace_bound_child(self) -> None:
        state = self.controller()
        first = state.authorize_send(authority_request(state))
        self.assertTrue(first["send_authorized"])
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "different worker"):
            state.authorize_send(
                authority_request(state, evidence=child_evidence(state, session_id="chrome-tab:9"))
            )
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("chrome-tab:5", snapshot.worker_session_ref.session_id)
        self.assertEqual("claimed", snapshot.delivery_state)

    def test_delivery_unknown_then_visible_reconciles_without_new_authority(self) -> None:
        state = self.controller()
        state.authorize_send(authority_request(state))
        unknown = state.record_delivery(
            {
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "task_sha256": TASK_SHA,
                "outcome": "unknown",
                "evidence_ref": "chatgpt-temporary:delivery:ambiguous:1",
            }
        )
        self.assertEqual("unknown", unknown["delivery_state"])
        denied = state.authorize_send(authority_request(state))
        self.assertFalse(denied["send_authorized"])
        delivered = state.record_delivery(
            {
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "task_sha256": TASK_SHA,
                "outcome": "delivered",
                "evidence_ref": "chatgpt-temporary:delivery:visible:2",
            }
        )
        self.assertEqual("delivered", delivered["delivery_state"])

    def test_capture_attestation_mismatch_cannot_record_terminal_result(self) -> None:
        state = self.controller()
        self.deliver(state)
        payload = "A bounded read-only research answer."
        wrong = runtime_report(**{"content.js": "f" * 64})
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "runtime attestation mismatch"):
            state.record_capture(
                {
                    "schema_version": 1,
                    "run_id": state.launch.run_id,
                    "delegation_id": state.launch.delegation_id,
                    "delivery_id": state.launch.delivery_id,
                    "result_text": result_text(state, payload),
                    "runtime_attestation": wrong,
                }
            )
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("delivered", snapshot.delivery_state)
        self.assertEqual("open", snapshot.result_state)

    def test_capture_records_normalized_generic_result_and_restart_reads_terminal_state(self) -> None:
        state = self.controller("first")
        self.deliver(state)
        payload = "A bounded read-only research answer."
        recorded = state.record_capture(
            {
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "result_text": result_text(state, payload),
                "runtime_attestation": runtime_report(),
            }
        )
        self.assertEqual("recorded", recorded["result_state"])
        self.assertRegex(recorded["runtime_attestation_sha256"], r"^[0-9a-f]{64}$")
        result = json.loads((self.output_root / "first" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), result["payload_sha256"])

        restarted = self.controller("second")
        self.assertFalse(restarted.launch.launch_now)
        self.assertTrue(restarted.done.is_set())
        recovered = json.loads((self.output_root / "second" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["delegation_id"], recovered["delegation_id"])
        self.assertEqual(result["payload_sha256"], recovered["payload_sha256"])

    def test_timeout_after_proven_delivery_closes_as_error_without_second_send(self) -> None:
        state = self.controller()
        self.deliver(state)
        self.assertTrue(state.record_timeout_if_delivered())
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("recorded", snapshot.result_state)
        self.assertEqual("ERROR", snapshot.result_status)
        denied = state.authorize_send(authority_request(state))
        self.assertFalse(denied["send_authorized"])


if __name__ == "__main__":
    unittest.main()
