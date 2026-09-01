from __future__ import annotations

import hashlib
import json
import tempfile
import threading
from pathlib import Path
from unittest import mock
import unittest

from runtime.control_plane import delegation_state


TASK_SHA = hashlib.sha256(b"bounded read-only worker task").hexdigest()


def identity_dict(**overrides: str) -> dict[str, str]:
    value = {
        "parent_task_id": "task-26-3c-next",
        "subgoal_id": "independent-research",
        "worker_kind": "researcher",
        "worker_profile": delegation_state.WORKER_PROFILE,
        "task_sha256": TASK_SHA,
        "result_contract_id": "research-result-v1",
    }
    value.update(overrides)
    return value


def session_ref(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "adapter_id": "chatgpt-temporary",
        "session_id": "temporary-chat-session-1",
        "conversation_id": "temporary-chat-conversation-1",
        "ownership": "manager_owned",
        "observation_ref": "agent-session:temporary-chat-session-1:observation:2",
    }
    value.update(overrides)
    return value


def result_value(
    prepared: delegation_state.PreparedDelegation,
    *,
    status: str = "COMPLETED",
    payload: str = "RESEARCH_RESULT_V1\nstatus=complete\nsummary=bounded result",
    **overrides: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "delegation_id": prepared.delegation_id,
        "delivery_id": prepared.delivery_id,
        "worker_kind": "researcher",
        "result_contract_id": "research-result-v1",
        "status": status,
        "payload": payload,
        "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    }
    value.update(overrides)
    return value


class DelegationStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_root = Path(self.temp.name) / "procedure-state"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def prepare(self) -> delegation_state.PreparedDelegation:
        return delegation_state.prepare_delegation(
            identity_dict(), state_root=self.state_root
        )

    def bind(self) -> delegation_state.PreparedDelegation:
        prepared = self.prepare()
        delegation_state.mark_launch_attempted(
            identity_dict(), run_id=prepared.run_id, state_root=self.state_root
        )
        delegation_state.bind_worker_session(
            identity_dict(),
            run_id=prepared.run_id,
            session_ref_value=session_ref(),
            state_root=self.state_root,
        )
        return prepared

    def deliver(self) -> delegation_state.PreparedDelegation:
        prepared = self.bind()
        claim = delegation_state.claim_delivery(
            identity_dict(), run_id=prepared.run_id, state_root=self.state_root
        )
        self.assertTrue(claim.claimed_now)
        delegation_state.record_delivery_outcome(
            identity_dict(),
            run_id=prepared.run_id,
            outcome="delivered",
            evidence_ref="agent-session:delivery:verified:1",
            state_root=self.state_root,
        )
        return prepared

    def _root(self) -> Path:
        return delegation_state._root(self.state_root)

    def test_identity_is_provider_independent_and_operation_key_is_deterministic(self) -> None:
        identity = delegation_state.parse_delegation_identity(identity_dict())
        first = delegation_state.delegation_operation_key(identity)
        second = delegation_state.delegation_operation_key(
            delegation_state.parse_delegation_identity(dict(identity_dict()))
        )
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertNotIn("adapter", identity.as_dict())
        self.assertNotIn("session", identity.as_dict())

    def test_prepare_creates_one_private_run_and_reuses_same_delegation(self) -> None:
        first = self.prepare()
        second = self.prepare()
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.delegation_id, second.delegation_id)
        self.assertEqual(first.delivery_id, second.delivery_id)
        self.assertEqual(first.run_id, second.run_id)
        self.assertRegex(first.run_id, r"^[0-9a-f]{64}$")
        self.assertRegex(first.delivery_id, r"^[0-9a-f]{64}$")
        snapshot = delegation_state.load_delegation(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("prepared", snapshot.launch_state)
        self.assertEqual("prepared", snapshot.delivery_state)
        self.assertEqual("open", snapshot.result_state)

    def test_first_profile_is_read_only_and_worker_session_must_be_manager_owned(self) -> None:
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "worker_profile must"
        ):
            delegation_state.parse_delegation_identity(
                identity_dict(worker_profile="mutating-worker-v1")
            )
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "manager_owned"
        ):
            delegation_state.parse_worker_session_ref(
                session_ref(ownership="user_owned")
            )

    def test_child_binding_requires_durable_launch_attempt_and_is_identity_stable(self) -> None:
        prepared = self.prepare()
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "before launch-attempted"
        ):
            delegation_state.bind_worker_session(
                identity_dict(),
                run_id=prepared.run_id,
                session_ref_value=session_ref(),
                state_root=self.state_root,
            )

        attempted = delegation_state.mark_launch_attempted(
            identity_dict(), run_id=prepared.run_id, state_root=self.state_root
        )
        self.assertEqual("launch-attempted", attempted.launch_state)
        bound = delegation_state.bind_worker_session(
            identity_dict(),
            run_id=prepared.run_id,
            session_ref_value=session_ref(),
            state_root=self.state_root,
        )
        self.assertEqual("child-bound", bound.launch_state)
        self.assertEqual("temporary-chat-session-1", bound.worker_session_ref.session_id)

        same = delegation_state.bind_worker_session(
            identity_dict(),
            run_id=prepared.run_id,
            session_ref_value=session_ref(),
            state_root=self.state_root,
        )
        self.assertEqual(bound.worker_session_ref, same.worker_session_ref)
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "different worker"
        ):
            delegation_state.bind_worker_session(
                identity_dict(),
                run_id=prepared.run_id,
                session_ref_value=session_ref(session_id="other-session"),
                state_root=self.state_root,
            )

    def test_delivery_claim_can_be_won_only_once(self) -> None:
        prepared = self.bind()
        first = delegation_state.claim_delivery(
            identity_dict(), run_id=prepared.run_id, state_root=self.state_root
        )
        second = delegation_state.claim_delivery(
            identity_dict(), run_id=prepared.run_id, state_root=self.state_root
        )
        self.assertTrue(first.claimed_now)
        self.assertFalse(second.claimed_now)
        self.assertEqual(first.delivery_id, second.delivery_id)
        self.assertEqual("claimed", second.delivery_state)

    def test_concurrent_delivery_contenders_never_both_win(self) -> None:
        prepared = self.bind()
        barrier = threading.Barrier(3)
        outcomes: list[bool | str] = []
        mutex = threading.Lock()

        def contender() -> None:
            barrier.wait()
            try:
                claim = delegation_state.claim_delivery(
                    identity_dict(),
                    run_id=prepared.run_id,
                    state_root=self.state_root,
                )
                result: bool | str = claim.claimed_now
            except BlockingIOError:
                result = "busy"
            with mutex:
                outcomes.append(result)

        threads = [threading.Thread(target=contender) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual(2, len(outcomes))
        self.assertEqual(1, sum(value is True for value in outcomes))
        self.assertEqual(0, sum(value is False for value in outcomes if value is True))
        snapshot = delegation_state.load_delegation(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("claimed", snapshot.delivery_state)

    def test_unknown_delivery_blocks_blind_reclaim_and_terminal_result(self) -> None:
        prepared = self.bind()
        delegation_state.claim_delivery(
            identity_dict(), run_id=prepared.run_id, state_root=self.state_root
        )
        unknown = delegation_state.record_delivery_outcome(
            identity_dict(),
            run_id=prepared.run_id,
            outcome="unknown",
            evidence_ref="agent-session:delivery:ambiguous:1",
            state_root=self.state_root,
        )
        self.assertEqual("unknown", unknown.delivery_state)
        retry = delegation_state.claim_delivery(
            identity_dict(), run_id=prepared.run_id, state_root=self.state_root
        )
        self.assertFalse(retry.claimed_now)
        self.assertEqual("unknown", retry.delivery_state)
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "undelivered delegation"
        ):
            delegation_state.record_worker_result(
                identity_dict(),
                run_id=prepared.run_id,
                result_value=result_value(prepared),
                state_root=self.state_root,
            )

    def test_terminal_result_is_correlated_bounded_and_idempotent(self) -> None:
        prepared = self.deliver()
        result = result_value(prepared)
        first = delegation_state.record_worker_result(
            identity_dict(),
            run_id=prepared.run_id,
            result_value=result,
            state_root=self.state_root,
        )
        second = delegation_state.record_worker_result(
            identity_dict(),
            run_id=prepared.run_id,
            result_value=result,
            state_root=self.state_root,
        )
        self.assertEqual("recorded", first.result_state)
        self.assertEqual("COMPLETED", first.result_status)
        self.assertEqual(first, second)

        changed_payload = "RESEARCH_RESULT_V1\nstatus=complete\nsummary=different"
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "different terminal result"
        ):
            delegation_state.record_worker_result(
                identity_dict(),
                run_id=prepared.run_id,
                result_value=result_value(prepared, payload=changed_payload),
                state_root=self.state_root,
            )

    def test_worker_result_rejects_wrong_delegation_delivery_contract_and_digest(self) -> None:
        prepared = self.deliver()
        cases = (
            ({"delegation_id": "a" * 64}, "delegation_id mismatch"),
            ({"delivery_id": "b" * 64}, "delivery_id mismatch"),
            ({"worker_kind": "reviewer"}, "worker_kind mismatch"),
            ({"result_contract_id": "review-result-v1"}, "contract mismatch"),
            ({"payload_sha256": "c" * 64}, "digest mismatch"),
        )
        for override, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(
                    delegation_state.DelegationStateError, message
                ):
                    delegation_state.record_worker_result(
                        identity_dict(),
                        run_id=prepared.run_id,
                        result_value=result_value(prepared, **override),
                        state_root=self.state_root,
                    )

    def test_wrong_private_run_capability_cannot_mutate_delegation(self) -> None:
        prepared = self.prepare()
        wrong = "f" * 64 if prepared.run_id != "f" * 64 else "e" * 64
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "run capability mismatch"
        ):
            delegation_state.mark_launch_attempted(
                identity_dict(), run_id=wrong, state_root=self.state_root
            )
        snapshot = delegation_state.load_delegation(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("prepared", snapshot.launch_state)

    def test_genesis_without_state_fails_closed_and_does_not_replace_run_identity(self) -> None:
        prepared = self.prepare()
        root = self._root()
        state_path = delegation_state._state_path(root, prepared.delegation_id)
        state_path.unlink()
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "genesis exists without mutable state"
        ):
            self.prepare()
        genesis = json.loads(
            delegation_state._genesis_path(root, prepared.delegation_id).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(prepared.run_id, genesis["run_id"])

    def test_corrupt_state_and_temp_residue_fail_closed(self) -> None:
        prepared = self.prepare()
        root = self._root()
        state_path = delegation_state._state_path(root, prepared.delegation_id)
        state_path.write_text("{not-json", encoding="utf-8")
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "state is invalid"
        ):
            self.prepare()

        state_path.unlink()
        delegation_state._genesis_path(root, prepared.delegation_id).unlink()
        residue = root / f".{prepared.delegation_id}.state.deadbeef.tmp"
        residue.write_bytes(b"untrusted residue")
        with self.assertRaisesRegex(
            delegation_state.DelegationStateError, "residue exists"
        ):
            self.prepare()

    def test_failed_state_replace_preserves_prior_valid_state_and_removes_temp(self) -> None:
        prepared = self.prepare()
        with mock.patch(
            "runtime.control_plane.delegation_state.os.replace",
            side_effect=OSError("injected replace failure"),
        ):
            with self.assertRaisesRegex(OSError, "injected replace failure"):
                delegation_state.mark_launch_attempted(
                    identity_dict(),
                    run_id=prepared.run_id,
                    state_root=self.state_root,
                )

        snapshot = delegation_state.load_delegation(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("prepared", snapshot.launch_state)
        self.assertEqual((), delegation_state._temp_paths(self._root(), prepared.delegation_id))


if __name__ == "__main__":
    unittest.main()
