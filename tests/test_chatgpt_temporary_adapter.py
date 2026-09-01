from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import unittest

from runtime.agent_sessions import chatgpt_temporary
from runtime.control_plane import delegation_state


TASK = "Compare two bounded public facts and return a concise read-only summary."
TASK_SHA = hashlib.sha256(TASK.encode("utf-8")).hexdigest()


def identity_dict(**overrides: str) -> dict[str, str]:
    value = {
        "parent_task_id": "manager-task-agent-session-1",
        "subgoal_id": "bounded-readonly-research",
        "worker_kind": "researcher",
        "worker_profile": delegation_state.WORKER_PROFILE,
        "task_sha256": TASK_SHA,
        "result_contract_id": "research-result-v1",
    }
    value.update(overrides)
    return value


class ChatGPTTemporaryAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_root = Path(self.temp.name) / "state"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def launch(self) -> chatgpt_temporary.TemporaryLaunchIntent:
        return chatgpt_temporary.prepare_temporary_launch(
            identity_dict(),
            task=TASK,
            state_root=self.state_root,
        )

    def child_evidence(self, launch: chatgpt_temporary.TemporaryLaunchIntent, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_version": 1,
            "adapter_id": chatgpt_temporary.ADAPTER_ID,
            "run_id": launch.run_id,
            "temporary_mode": True,
            "fresh_context": True,
            "personalization_disabled": True,
            "plugin_markers": [],
            "session_id": "chrome-tab:41",
            "conversation_id": None,
            "observation_ref": "chatgpt-temporary:tab:41:pre-send:1",
        }
        value.update(overrides)
        return value

    def bind_and_claim(self, launch: chatgpt_temporary.TemporaryLaunchIntent) -> None:
        chatgpt_temporary.bind_temporary_child(
            identity_dict(),
            evidence_value=self.child_evidence(launch),
            state_root=self.state_root,
        )
        claim = chatgpt_temporary.claim_temporary_delivery(
            identity_dict(), run_id=launch.run_id, state_root=self.state_root
        )
        self.assertTrue(claim.claimed_now)

    def delivered(self, launch: chatgpt_temporary.TemporaryLaunchIntent) -> None:
        self.bind_and_claim(launch)
        snapshot = chatgpt_temporary.record_temporary_delivery(
            identity_dict(),
            evidence_value={
                "schema_version": 1,
                "run_id": launch.run_id,
                "delegation_id": launch.delegation_id,
                "delivery_id": launch.delivery_id,
                "task_sha256": TASK_SHA,
                "outcome": "delivered",
                "evidence_ref": "chatgpt-temporary:delivery:visible-user-turn:1",
            },
            state_root=self.state_root,
        )
        self.assertEqual("delivered", snapshot.delivery_state)

    def result_text(self, launch: chatgpt_temporary.TemporaryLaunchIntent, **overrides: object) -> str:
        value: dict[str, object] = {
            "schema_version": 1,
            "delegation_id": launch.delegation_id,
            "delivery_id": launch.delivery_id,
            "worker_kind": "researcher",
            "result_contract_id": "research-result-v1",
            "status": "COMPLETED",
            "payload": "Bounded result from the fresh read-only child.",
        }
        value.update(overrides)
        return (
            chatgpt_temporary.RAW_RESULT_BEGIN
            + "\n"
            + json.dumps(value, separators=(",", ":"), ensure_ascii=False)
            + "\n"
            + chatgpt_temporary.RAW_RESULT_END
        )

    def test_prepare_commits_launch_attempt_before_returning_browser_intent(self) -> None:
        launch = self.launch()
        self.assertTrue(launch.launch_now)
        self.assertEqual("launch-attempted", launch.launch_state)
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("launch-attempted", snapshot.launch_state)
        self.assertEqual("prepared", snapshot.delivery_state)
        parsed = urlparse(launch.launch_url)
        query = parse_qs(parsed.query)
        fragment = parse_qs(parsed.fragment)
        self.assertEqual("https", parsed.scheme)
        self.assertEqual("chatgpt.com", parsed.netloc)
        self.assertEqual(["true"], query["temporary-chat"])
        self.assertEqual(["1"], query["cap_agent_delegate"])
        self.assertNotIn("cap_run_id", query)
        self.assertEqual([launch.run_id], fragment["cap_run_id"])
        self.assertEqual([launch.delegation_id], query["cap_delegation_id"])
        self.assertEqual([launch.delivery_id], query["cap_delivery_id"])
        self.assertEqual([TASK_SHA], query["cap_task_sha256"])
        prompt = query["prompt"][0]
        self.assertIn("WORKER_TASK_V1", prompt)
        self.assertIn(f"delegation_id={launch.delegation_id}", prompt)
        self.assertIn(f"delivery_id={launch.delivery_id}", prompt)
        self.assertNotIn(launch.run_id, prompt)
        self.assertEqual(hashlib.sha256(prompt.encode("utf-8")).hexdigest(), launch.prompt_sha256)

    def test_prepare_rejects_task_identity_mismatch_and_never_commits_launch(self) -> None:
        wrong = identity_dict(task_sha256="b" * 64)
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "task digest"):
            chatgpt_temporary.prepare_temporary_launch(
                wrong, task=TASK, state_root=self.state_root
            )
        prepared = delegation_state.prepare_delegation(wrong, state_root=self.state_root)
        self.assertEqual("prepared", prepared.launch_state)

    def test_restart_recovers_same_private_run_but_never_reauthorizes_browser_launch(self) -> None:
        first = self.launch()
        second = self.launch()
        self.assertTrue(first.launch_now)
        self.assertFalse(second.launch_now)
        self.assertEqual(first.run_id, second.run_id)
        self.assertEqual(first.delegation_id, second.delegation_id)
        self.assertEqual(first.delivery_id, second.delivery_id)
        self.assertEqual(first.launch_url, second.launch_url)
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("launch-attempted", snapshot.launch_state)

    def test_child_binding_requires_positive_fresh_temporary_nonpersonalized_evidence(self) -> None:
        launch = self.launch()
        cases = (
            ({"temporary_mode": False}, "Temporary Chat mode"),
            ({"fresh_context": False}, "fresh child context"),
            ({"personalization_disabled": False}, "non-personalized"),
            ({"plugin_markers": ["GitHub"]}, "no plugin/app markers"),
            ({"adapter_id": "other-adapter"}, "schema or adapter mismatch"),
        )
        for override, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(delegation_state.DelegationStateError, message):
                    chatgpt_temporary.bind_temporary_child(
                        identity_dict(),
                        evidence_value=self.child_evidence(launch, **override),
                        state_root=self.state_root,
                    )
        bound = chatgpt_temporary.bind_temporary_child(
            identity_dict(),
            evidence_value=self.child_evidence(launch),
            state_root=self.state_root,
        )
        self.assertEqual("child-bound", bound.launch_state)
        self.assertEqual(chatgpt_temporary.ADAPTER_ID, bound.worker_session_ref.adapter_id)

    def test_local_delivery_authority_is_one_shot(self) -> None:
        launch = self.launch()
        chatgpt_temporary.bind_temporary_child(
            identity_dict(),
            evidence_value=self.child_evidence(launch),
            state_root=self.state_root,
        )
        first = chatgpt_temporary.claim_temporary_delivery(
            identity_dict(), run_id=launch.run_id, state_root=self.state_root
        )
        second = chatgpt_temporary.claim_temporary_delivery(
            identity_dict(), run_id=launch.run_id, state_root=self.state_root
        )
        self.assertTrue(first.claimed_now)
        self.assertFalse(second.claimed_now)
        self.assertEqual("claimed", second.delivery_state)

    def test_restart_after_delivery_is_monitor_only_and_preserves_same_delivery(self) -> None:
        launch = self.launch()
        self.delivered(launch)
        resumed = self.launch()
        self.assertFalse(resumed.launch_now)
        self.assertEqual(launch.run_id, resumed.run_id)
        self.assertEqual(launch.delivery_id, resumed.delivery_id)
        snapshot = delegation_state.load_delegation(identity_dict(), state_root=self.state_root)
        self.assertEqual("delivered", snapshot.delivery_state)

    def test_unknown_delivery_never_reclaims_and_reconciles_same_delivery(self) -> None:
        launch = self.launch()
        self.bind_and_claim(launch)
        unknown = chatgpt_temporary.record_temporary_delivery(
            identity_dict(),
            evidence_value={
                "schema_version": 1,
                "run_id": launch.run_id,
                "delegation_id": launch.delegation_id,
                "delivery_id": launch.delivery_id,
                "task_sha256": TASK_SHA,
                "outcome": "unknown",
                "evidence_ref": "chatgpt-temporary:delivery:ambiguous:1",
            },
            state_root=self.state_root,
        )
        self.assertEqual("unknown", unknown.delivery_state)
        retry = chatgpt_temporary.claim_temporary_delivery(
            identity_dict(), run_id=launch.run_id, state_root=self.state_root
        )
        self.assertFalse(retry.claimed_now)
        reconciled = chatgpt_temporary.record_temporary_delivery(
            identity_dict(),
            evidence_value={
                "schema_version": 1,
                "run_id": launch.run_id,
                "delegation_id": launch.delegation_id,
                "delivery_id": launch.delivery_id,
                "task_sha256": TASK_SHA,
                "outcome": "delivered",
                "evidence_ref": "chatgpt-temporary:delivery:reconciled:2",
            },
            state_root=self.state_root,
        )
        self.assertEqual("delivered", reconciled.delivery_state)

    def test_adapter_computes_payload_hash_and_records_one_correlated_result(self) -> None:
        launch = self.launch()
        self.delivered(launch)
        text = self.result_text(launch)
        normalized = chatgpt_temporary.normalize_worker_result_text(
            text,
            identity=launch.identity,
            delegation_id=launch.delegation_id,
            delivery_id=launch.delivery_id,
        )
        expected_hash = hashlib.sha256(
            b"Bounded result from the fresh read-only child."
        ).hexdigest()
        self.assertEqual(expected_hash, normalized.value["payload_sha256"])
        terminal = chatgpt_temporary.record_temporary_worker_result(
            identity_dict(),
            run_id=launch.run_id,
            result_text=text,
            state_root=self.state_root,
        )
        self.assertEqual("recorded", terminal.result_state)
        self.assertEqual("COMPLETED", terminal.result_status)
        replay = chatgpt_temporary.record_temporary_worker_result(
            identity_dict(),
            run_id=launch.run_id,
            result_text=text,
            state_root=self.state_root,
        )
        self.assertEqual(terminal, replay)

    def test_result_parser_rejects_foreign_or_ambiguous_child_output(self) -> None:
        launch = self.launch()
        self.delivered(launch)
        bad_delivery = self.result_text(launch, delivery_id="c" * 64)
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "delivery_id mismatch"):
            chatgpt_temporary.record_temporary_worker_result(
                identity_dict(),
                run_id=launch.run_id,
                result_text=bad_delivery,
                state_root=self.state_root,
            )
        duplicate = self.result_text(launch) + "\n" + self.result_text(launch)
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "exactly one"):
            chatgpt_temporary.record_temporary_worker_result(
                identity_dict(),
                run_id=launch.run_id,
                result_text=duplicate,
                state_root=self.state_root,
            )
        wrapped = "extra\n" + self.result_text(launch)
        with self.assertRaisesRegex(delegation_state.DelegationStateError, "outside structured block"):
            chatgpt_temporary.record_temporary_worker_result(
                identity_dict(),
                run_id=launch.run_id,
                result_text=wrapped,
                state_root=self.state_root,
            )


if __name__ == "__main__":
    unittest.main()
