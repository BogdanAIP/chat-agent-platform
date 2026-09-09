from __future__ import annotations

import hashlib
import json
import tempfile
import threading
from pathlib import Path
import unittest

from runtime.agent_sessions import chatgpt_temporary, source_attestation
from runtime.agent_sessions.chatgpt_temporary_controller import (
    TemporaryControllerRuntime,
    TemporaryControllerState,
)
from runtime.control_plane import delegation_state


TASK = "Read the supplied bounded question and return a short research summary without changing external state."
TASK_SHA = hashlib.sha256(TASK.encode("utf-8")).hexdigest()
EXECUTION_GENERATION = "9" * 64
LAUNCH_HANDLE = "7" * 64
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


def expected_runtime_attestation(head: str = "a" * 40) -> dict[str, object]:
    return {
        "schema_version": 1,
        "adapter_id": source_attestation.ADAPTER_ID,
        "expected_head": head,
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
    expected_head: str | None = None,
    prompt_sha256: str | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": state.launch.run_id,
        "delegation_id": state.launch.delegation_id,
        "delivery_id": state.launch.delivery_id,
        "expected_runtime_head": expected_head or state.expected_runtime_attestation.expected_head,
        "prompt_sha256": prompt_sha256 or state.launch.prompt_sha256,
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

    def controller(self, suffix: str = "first", *, head: str = "a" * 40) -> TemporaryControllerState:
        return TemporaryControllerState(
            identity_value=identity_dict(),
            task=TASK,
            launch_handle=LAUNCH_HANDLE,
            expected_runtime_attestation_value=expected_runtime_attestation(head),
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

    def cleanup_token(self, state: TemporaryControllerState) -> str:
        response = state.record_event(
            {
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
            }
        )
        token = response.get("cleanup_token")
        self.assertIsInstance(token, str)
        self.assertEqual(64, len(token))
        return token

    def prepare_capture(self, state: TemporaryControllerState, cleanup_token: str) -> str:
        response = state.prepare_capture(
            {
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "cleanup_token": cleanup_token,
                "runtime_attestation": runtime_report(),
            }
        )
        token = response.get("capture_token")
        self.assertIsInstance(token, str)
        self.assertEqual(64, len(token))
        return token

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
        self.assertIn("cap_expected_head=" + "a" * 40, launch["launch_url"])
        self.assertIn("cap_prompt_sha256=", launch["launch_url"])
        self.assertNotIn(first.launch.run_id, launch["launch_url"])

    def test_browser_claim_must_be_committed_before_local_send_authority(self) -> None:
        state = self.controller()
        request = authority_request(state)
        request["browser_claim_committed"] = False
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "browser send claim"):
            state.authorize_send(request)
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("launch-attempted", snapshot.launch_state)
        self.assertEqual("prepared", snapshot.delivery_state)

    def test_prebind_cross_head_old_launch_provenance_is_rejected_before_worker_binding(self) -> None:
        first = self.controller("head-a", head="a" * 40)
        first_prompt = first.launch.prompt_sha256
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("launch-attempted", snapshot.launch_state)
        self.assertIsNone(snapshot.worker_session_ref)

        second = self.controller("head-b", head="b" * 40)
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "expected runtime HEAD mismatch"):
            second.authorize_send(
                authority_request(
                    second,
                    expected_head="a" * 40,
                    prompt_sha256=first_prompt,
                )
            )
        after = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("launch-attempted", after.launch_state)
        self.assertEqual("prepared", after.delivery_state)
        self.assertIsNone(after.worker_session_ref)

    def test_wrong_prompt_digest_is_rejected_before_worker_binding(self) -> None:
        state = self.controller()
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "launch prompt digest mismatch"):
            state.authorize_send(authority_request(state, prompt_sha256="f" * 64))
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertIsNone(snapshot.worker_session_ref)
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
        self.assertEqual(f"chatgpt-delivery:{state.launch.delivery_id}", snapshot.worker_session_ref.session_id)
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

    def test_changed_numeric_tab_id_rebinds_same_delivery_child_without_second_send(self) -> None:
        state = self.controller()
        first = state.authorize_send(authority_request(state))
        self.assertTrue(first["send_authorized"])
        second = state.authorize_send(
            authority_request(state, evidence=child_evidence(state, session_id="chrome-tab:9"))
        )
        self.assertFalse(second["send_authorized"])
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual(f"chatgpt-delivery:{state.launch.delivery_id}", snapshot.worker_session_ref.session_id)
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

    def test_capture_requires_cleanup_ack_runtime_prepare_and_one_time_commit_token(self) -> None:
        state = self.controller()
        self.deliver(state)
        payload = "A bounded read-only research answer."

        with self.assertRaisesRegex(delegation_state.DelegationStateError, "cleanup token"):
            state.prepare_capture(
                {
                    "schema_version": 1,
                    "run_id": state.launch.run_id,
                    "delegation_id": state.launch.delegation_id,
                    "delivery_id": state.launch.delivery_id,
                    "cleanup_token": "0" * 64,
                    "runtime_attestation": runtime_report(),
                }
            )

        cleanup = self.cleanup_token(state)
        capture = self.prepare_capture(state, cleanup)
        recorded = state.record_capture(
            {
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "cleanup_token": cleanup,
                "capture_token": capture,
                "result_text": result_text(state, payload),
            }
        )
        self.assertEqual("recorded", recorded["result_state"])
        self.assertIsNone(state.capture_token)
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "stale or missing"):
            state.record_capture(
                {
                    "schema_version": 1,
                    "run_id": state.launch.run_id,
                    "delegation_id": state.launch.delegation_id,
                    "delivery_id": state.launch.delivery_id,
                    "cleanup_token": cleanup,
                    "capture_token": capture,
                    "result_text": result_text(state, payload),
                }
            )

    def test_capture_attestation_mismatch_fails_during_prepare_before_terminal_record(self) -> None:
        state = self.controller()
        self.deliver(state)
        cleanup = self.cleanup_token(state)
        wrong = runtime_report(**{"content.js": "f" * 64})
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "runtime attestation mismatch"):
            state.prepare_capture(
                {
                    "schema_version": 1,
                    "run_id": state.launch.run_id,
                    "delegation_id": state.launch.delegation_id,
                    "delivery_id": state.launch.delivery_id,
                    "cleanup_token": cleanup,
                    "runtime_attestation": wrong,
                }
            )
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("delivered", snapshot.delivery_state)
        self.assertEqual("open", snapshot.result_state)

    def test_capture_records_result_and_restart_reads_terminal_state(self) -> None:
        state = self.controller("first")
        self.deliver(state)
        cleanup = self.cleanup_token(state)
        capture = self.prepare_capture(state, cleanup)
        payload = "A bounded read-only research answer."
        state.record_capture(
            {
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "cleanup_token": cleanup,
                "capture_token": capture,
                "result_text": result_text(state, payload),
            }
        )
        result = json.loads((self.output_root / "first" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), result["payload_sha256"])

        restarted = self.controller("second")
        self.assertFalse(restarted.launch.launch_now)
        self.assertTrue(restarted.done.is_set())
        recovered = json.loads((self.output_root / "second" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["delegation_id"], recovered["delegation_id"])
        self.assertEqual(result["payload_sha256"], recovered["payload_sha256"])

    def test_timeout_request_does_not_close_delivered_open_without_final_observation(self) -> None:
        state = self.controller()
        self.deliver(state)
        request_id = state.request_final_observation_if_delivered()
        self.assertRegex(request_id or "", r"^[0-9a-f]{64}$")
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("delivered", snapshot.delivery_state)
        self.assertEqual("open", snapshot.result_state)
        self.assertFalse(state.done.is_set())

    def test_final_observation_with_visible_terminal_result_leaves_slot_open_for_capture(self) -> None:
        state = self.controller()
        self.deliver(state)
        request_id = state.request_final_observation_if_delivered()
        response = state.record_final_observation(
            {
                "schema_version": 1,
                "run_id": state.launch.run_id,
                "delegation_id": state.launch.delegation_id,
                "delivery_id": state.launch.delivery_id,
                "request_id": request_id,
                "terminal_result_visible": True,
                "worker_generating": False,
                "runtime_attestation": runtime_report(),
            }
        )
        self.assertEqual("terminal-visible-awaiting-capture", response["status"])
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("open", snapshot.result_state)
        self.assertFalse(state.done.is_set())

    def test_final_observation_without_terminal_result_preserves_unresolved_state(self) -> None:
        state = self.controller()
        self.deliver(state)
        request_id = state.request_final_observation_if_delivered()
        for generating in (True, False):
            response = state.record_final_observation(
                {
                    "schema_version": 1,
                    "run_id": state.launch.run_id,
                    "delegation_id": state.launch.delegation_id,
                    "delivery_id": state.launch.delivery_id,
                    "request_id": request_id,
                    "terminal_result_visible": False,
                    "worker_generating": generating,
                    "runtime_attestation": runtime_report(),
                }
            )
            self.assertEqual("unresolved-awaiting-worker-result", response["status"])
            self.assertEqual("generating" if generating else "no-terminal-result", response["observation"])
            snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
            self.assertEqual("delivered", snapshot.delivery_state)
            self.assertEqual("open", snapshot.result_state)
            self.assertIsNone(snapshot.result_status)
            self.assertFalse(state.done.is_set())
            self.assertFalse((self.output_root / "first" / "result.json").exists())
        denied = state.authorize_send(authority_request(state))
        self.assertFalse(denied["send_authorized"])


class TemporaryControllerPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.state_root = root / "private-state"
        self.output_root = root / "output"
        self.runtime = TemporaryControllerRuntime(
            identity_value=identity_dict(),
            task=TASK,
            expected_runtime_attestation_value=expected_runtime_attestation(),
            state_root=self.state_root,
            output_dir=self.output_root,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def preflight_request(self) -> dict[str, object]:
        assert self.runtime.preflight_id is not None
        return {
            "schema_version": 1,
            "preflight_id": self.runtime.preflight_id,
            "execution_generation": EXECUTION_GENERATION,
            "runtime_attestation": runtime_report(),
        }

    def test_initial_runtime_exposes_only_neutral_preflight_while_durable_launch_stays_prepared(self) -> None:
        self.assertEqual("preflight", self.runtime.health()["status"])
        self.assertIsNone(self.runtime.state)
        self.assertFalse((self.output_root / "launch.json").exists())
        preflight = json.loads((self.output_root / "preflight.json").read_text(encoding="utf-8"))
        self.assertRegex(preflight["preflight_url"], r"^https://chatgpt\.com/\?cap_agent_preflight=1#cap_preflight_id=[0-9a-f]{64}$")
        self.assertNotIn("cap_run_id", preflight["preflight_url"])
        self.assertNotIn("prompt=", preflight["preflight_url"])
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("prepared", snapshot.launch_state)

    def test_prepare_handoff_still_leaves_durable_launch_prepared(self) -> None:
        prepared = self.runtime.prepare_live_handoff(self.preflight_request())
        self.assertEqual("handoff-prepared", prepared["status"])
        self.assertRegex(prepared["launch_handle"], r"^[0-9a-f]{64}$")
        self.assertRegex(prepared["run_id"], r"^[0-9a-f]{64}$")
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("prepared", snapshot.launch_state)
        self.assertFalse((self.output_root / "launch.json").exists())

    def test_commit_after_live_handoff_creates_one_task_launch_without_private_run_in_projection(self) -> None:
        prepared = self.runtime.prepare_live_handoff(self.preflight_request())
        commit = self.preflight_request()
        commit["launch_handle"] = prepared["launch_handle"]
        committed = self.runtime.commit_live_handoff(commit)
        self.assertEqual("launch-committed", committed["status"])
        self.assertEqual("launch-attempted", committed["launch_state"])
        state = self.runtime.require_state()
        self.assertTrue(state.launch.launch_now)
        launch = json.loads((self.output_root / "launch.json").read_text(encoding="utf-8"))
        self.assertNotIn("run_id", launch)
        self.assertNotIn(prepared["run_id"], launch["launch_url"])
        self.assertIn(str(prepared["launch_handle"]), launch["launch_url"])
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("launch-attempted", snapshot.launch_state)


if __name__ == "__main__":
    unittest.main()
