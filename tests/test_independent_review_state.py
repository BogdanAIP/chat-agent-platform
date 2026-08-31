from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import mock
import unittest

from runtime.control_plane import independent_review_state as review_state


BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40


def identity_dict() -> dict[str, object]:
    return {
        "repository": "BogdanAIP/chat-agent-platform",
        "pr_number": 141,
        "base_sha": BASE_SHA,
        "head_sha": HEAD_SHA,
        "review_skill": "code-review",
        "review_skill_version": "1.1",
    }


def review_result(
    *,
    status: str = "PASS",
    findings: int = 0,
    rejected: int = 3,
    review_run_id: str | None = None,
    suffix: str = "",
) -> str:
    validity = "CURRENT" if status in {"PASS", "FINDINGS", "ABSTAIN"} else "STALE_MATERIAL_CHANGE"
    lines = [
        "REVIEW_RESULT_V1",
        "repository=BogdanAIP/chat-agent-platform",
        "pr_number=141",
        f"base_sha={BASE_SHA}",
        f"head_sha={HEAD_SHA}",
        f"review_policy_ref={BASE_SHA}",
        "review_skill=code-review",
        "review_skill_version=1.1",
        "review_context=ordinary_chat_fresh",
        f"status={status}",
        f"review_validity={validity}",
        f"reported_findings={findings}",
        f"rejected_candidates={rejected}",
        "reviewed_at=2026-08-31T08:30:48+00:00",
    ]
    if review_run_id is not None:
        lines.append(f"review_run_id={review_run_id}")
    if suffix:
        lines.extend(["", suffix])
    return "\n".join(lines)


class IndependentReviewStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_root = Path(self.temp.name) / "procedure-state"
        self.identity = review_state.parse_review_identity(identity_dict())
        self.operation_key = review_state.review_operation_key(self.identity)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def prepare(self) -> review_state.PreparedReviewOperation:
        return review_state.prepare_review_operation(identity_dict(), state_root=self.state_root)

    def dispatch(self) -> review_state.PreparedReviewOperation:
        prepared = self.prepare()
        summary = review_state.mark_dispatch_attempted(identity_dict(), state_root=self.state_root)
        self.assertEqual("dispatch-attempted", summary["dispatch_state"])
        return prepared

    def _root(self) -> Path:
        return review_state._review_root(self.state_root)

    def _write_genesis_only(self, *, nonce: str = "a" * 64) -> str:
        root = self._root()
        genesis = review_state._build_genesis(self.identity, self.operation_key, nonce)
        review_state._exclusive_create_file(
            review_state._genesis_path(root, self.operation_key),
            review_state._encode_json(genesis),
        )
        return nonce

    def _load_durable_pair(self) -> tuple[dict[str, object], dict[str, object]]:
        root = self._root()
        genesis = json.loads(
            review_state._genesis_path(root, self.operation_key).read_text(encoding="utf-8")
        )
        state = json.loads(
            review_state._state_path(root, self.operation_key).read_text(encoding="utf-8")
        )
        return genesis, state

    def test_operation_key_is_deterministic_full_sha256(self) -> None:
        first = review_state.review_operation_key(self.identity)
        second = review_state.review_operation_key(
            review_state.parse_review_identity(dict(identity_dict()))
        )
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertEqual(32, len(review_state._lock_id(first)))

    def test_prepare_creates_one_nonce_and_reuses_prepared_operation(self) -> None:
        first = self.prepare()
        second = self.prepare()
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.operation_key, second.operation_key)
        self.assertEqual(first.review_run_id, second.review_run_id)
        self.assertRegex(first.review_run_id, r"^[0-9a-f]{64}$")
        genesis, state = self._load_durable_pair()
        self.assertEqual(first.review_run_id, genesis["review_run_id"])
        self.assertEqual(first.review_run_id, state["review_run_id"])
        self.assertEqual("prepared", state["dispatch_state"])
        self.assertEqual("open", state["result_state"])

    def test_dispatch_attempt_is_durable_and_cannot_repeat(self) -> None:
        prepared = self.dispatch()
        with self.assertRaisesRegex(review_state.ReviewStateError, "already attempted"):
            review_state.mark_dispatch_attempted(identity_dict(), state_root=self.state_root)
        again = self.prepare()
        self.assertEqual(prepared.review_run_id, again.review_run_id)
        self.assertEqual("dispatch-attempted", again.dispatch_state)

    def test_pending_reconcile_never_exposes_private_nonce(self) -> None:
        self.dispatch()
        response = review_state.reconcile_independent_review_result(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("pending", response["status"])
        self.assertNotIn("review_run_id", response)
        self.assertNotIn("result", response)

    def test_automatic_submit_records_exact_result_and_is_idempotent_after_lost_ack(self) -> None:
        prepared = self.dispatch()
        payload = review_result(review_run_id=prepared.review_run_id)
        request = {"review_run_id": prepared.review_run_id, "result": payload}
        first = review_state.submit_independent_review_result(request, state_root=self.state_root)
        second = review_state.submit_independent_review_result(request, state_root=self.state_root)
        self.assertEqual("recorded", first["status"])
        self.assertEqual("already_recorded", second["status"])
        self.assertEqual(first["result_body_sha256"], second["result_body_sha256"])

        consumed = review_state.reconcile_independent_review_result(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("automatic-result-recorded", consumed["result_state"])
        self.assertEqual("automatic", consumed["result_source"])
        self.assertEqual(payload, consumed["result"])
        # Exposure after durable result closure is allowed; the payload itself
        # intentionally contains the exact automatic review_run_id.
        self.assertIn(prepared.review_run_id, consumed["result"])

    def test_automatic_submit_rejects_wrong_nonce_and_different_digest(self) -> None:
        prepared = self.dispatch()
        good = review_result(review_run_id=prepared.review_run_id)
        wrong_nonce = "b" * 64 if prepared.review_run_id != "b" * 64 else "c" * 64
        with self.assertRaisesRegex(review_state.ReviewStateError, "immutable genesis"):
            review_state.submit_independent_review_result(
                {
                    "review_run_id": wrong_nonce,
                    "result": review_result(review_run_id=wrong_nonce),
                },
                state_root=self.state_root,
            )

        review_state.submit_independent_review_result(
            {"review_run_id": prepared.review_run_id, "result": good},
            state_root=self.state_root,
        )
        changed = review_result(
            review_run_id=prepared.review_run_id,
            suffix="Same header, materially different explanatory body.",
        )
        with self.assertRaisesRegex(review_state.ReviewStateError, "different digest"):
            review_state.submit_independent_review_result(
                {"review_run_id": prepared.review_run_id, "result": changed},
                state_root=self.state_root,
            )

    def test_automatic_submit_requires_dispatch_attempted(self) -> None:
        prepared = self.prepare()
        with self.assertRaisesRegex(review_state.ReviewStateError, "before dispatch-attempted"):
            review_state.submit_independent_review_result(
                {
                    "review_run_id": prepared.review_run_id,
                    "result": review_result(review_run_id=prepared.review_run_id),
                },
                state_root=self.state_root,
            )

    def test_manual_fallback_closes_automatic_submission(self) -> None:
        prepared = self.dispatch()
        manual = review_result(suffix="Manual fresh-review evidence.")
        closed = review_state.reconcile_independent_review_result(
            {**identity_dict(), "manual_result": manual},
            state_root=self.state_root,
        )
        self.assertEqual("manual-fallback-recorded", closed["result_state"])
        self.assertEqual("manual", closed["result_source"])
        with self.assertRaisesRegex(review_state.ReviewStateError, "closed by manual fallback"):
            review_state.submit_independent_review_result(
                {
                    "review_run_id": prepared.review_run_id,
                    "result": review_result(review_run_id=prepared.review_run_id),
                },
                state_root=self.state_root,
            )

    def test_automatic_result_wins_if_it_commits_before_manual_fallback(self) -> None:
        prepared = self.dispatch()
        automatic = review_result(review_run_id=prepared.review_run_id)
        review_state.submit_independent_review_result(
            {"review_run_id": prepared.review_run_id, "result": automatic},
            state_root=self.state_root,
        )
        manual = review_result(suffix="A distinct complete manual PASS that lost the race.")
        reconciled = review_state.reconcile_independent_review_result(
            {**identity_dict(), "manual_result": manual},
            state_root=self.state_root,
        )
        self.assertEqual("automatic-result-recorded", reconciled["result_state"])
        self.assertEqual(automatic, reconciled["result"])
        self.assertFalse(reconciled["manual_result_recorded"])
        self.assertEqual(
            "automatic_result_already_authoritative",
            reconciled["manual_result_rejection"],
        )

    def test_genesis_only_state_requires_manual_recovery_and_never_recreates_nonce(self) -> None:
        nonce = self._write_genesis_only()
        pending = review_state.reconcile_independent_review_result(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("manual_recovery_required", pending["status"])
        self.assertFalse(pending["automatic_submission_open"])
        self.assertFalse(pending["automatic_relaunch_allowed"])
        self.assertNotIn("review_run_id", pending)
        with self.assertRaisesRegex(review_state.ReviewStateError, "manual_recovery_required"):
            self.prepare()

        manual = review_result(suffix="Fresh manual result after genesis-only crash.")
        recovered = review_state.reconcile_independent_review_result(
            {**identity_dict(), "manual_result": manual},
            state_root=self.state_root,
        )
        self.assertEqual("automation-abandoned", recovered["dispatch_state"])
        self.assertEqual("manual-fallback-recorded", recovered["result_state"])
        self.assertEqual("state-missing-after-genesis", recovered["recovery_reason"])
        genesis, state = self._load_durable_pair()
        self.assertEqual(nonce, genesis["review_run_id"])
        self.assertEqual(nonce, state["review_run_id"])

        with self.assertRaisesRegex(review_state.ReviewStateError, "closed by manual fallback"):
            review_state.submit_independent_review_result(
                {
                    "review_run_id": nonce,
                    "result": review_result(review_run_id=nonce),
                },
                state_root=self.state_root,
            )

    def test_genesis_plus_temp_residue_allows_only_manual_terminal_recovery(self) -> None:
        nonce = self._write_genesis_only()
        root = self._root()
        residue = root / f".{self.operation_key}.state.deadbeef.tmp"
        residue.write_text("partial state that is never trusted", encoding="utf-8")
        pending = review_state.reconcile_independent_review_result(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual(1, pending["temp_residue_count"])
        self.assertEqual("manual_recovery_required", pending["status"])

        recovered = review_state.reconcile_independent_review_result(
            {**identity_dict(), "manual_result": review_result()},
            state_root=self.state_root,
        )
        self.assertEqual("automation-abandoned", recovered["dispatch_state"])
        self.assertTrue(residue.exists(), "forensic temp residue must not be promoted or silently rewritten")
        genesis, state = self._load_durable_pair()
        self.assertEqual(nonce, genesis["review_run_id"])
        self.assertEqual(nonce, state["review_run_id"])

    def test_existing_corrupt_canonical_is_not_silently_recovered(self) -> None:
        self.prepare()
        state_path = review_state._state_path(self._root(), self.operation_key)
        state_path.write_text("{not-json", encoding="utf-8")
        with self.assertRaisesRegex(review_state.ReviewStateError, "state is invalid"):
            review_state.reconcile_independent_review_result(
                {**identity_dict(), "manual_result": review_result()},
                state_root=self.state_root,
            )
        self.assertEqual("{not-json", state_path.read_text(encoding="utf-8"))

    def test_state_identity_or_nonce_mismatch_blocks_manual_overwrite(self) -> None:
        prepared = self.prepare()
        state_path = review_state._state_path(self._root(), self.operation_key)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["review_run_id"] = "d" * 64 if prepared.review_run_id != "d" * 64 else "e" * 64
        state_path.write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaisesRegex(review_state.ReviewStateError, "nonce mismatch"):
            review_state.reconcile_independent_review_result(
                {**identity_dict(), "manual_result": review_result()},
                state_root=self.state_root,
            )

    def test_failed_atomic_replace_leaves_old_valid_canonical_state(self) -> None:
        self.prepare()
        module_os_replace = "runtime.control_plane.independent_review_state.os.replace"
        with mock.patch(module_os_replace, side_effect=OSError("injected replace failure")):
            with self.assertRaisesRegex(OSError, "injected replace failure"):
                review_state.mark_dispatch_attempted(identity_dict(), state_root=self.state_root)

        pending = review_state.reconcile_independent_review_result(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("pending", pending["status"])
        self.assertEqual("prepared", pending["dispatch_state"])
        self.assertEqual((), review_state._state_temp_paths(self._root(), self.operation_key))

    def test_manual_result_cannot_smuggle_automatic_run_id(self) -> None:
        prepared = self.prepare()
        with self.assertRaisesRegex(review_state.ReviewStateError, "unsupported field review_run_id"):
            review_state.reconcile_independent_review_result(
                {
                    **identity_dict(),
                    "manual_result": review_result(review_run_id=prepared.review_run_id),
                },
                state_root=self.state_root,
            )

    def test_result_validation_rejects_wrong_policy_context_and_pass_findings(self) -> None:
        prepared = self.dispatch()
        wrong_policy = review_result(review_run_id=prepared.review_run_id).replace(
            f"review_policy_ref={BASE_SHA}", f"review_policy_ref={HEAD_SHA}"
        )
        with self.assertRaisesRegex(review_state.ReviewStateError, "policy ref"):
            review_state.submit_independent_review_result(
                {"review_run_id": prepared.review_run_id, "result": wrong_policy},
                state_root=self.state_root,
            )

        invalid_pass = review_result(review_run_id=prepared.review_run_id).replace(
            "reported_findings=0", "reported_findings=1"
        )
        with self.assertRaisesRegex(review_state.ReviewStateError, "PASS requires"):
            review_state.submit_independent_review_result(
                {"review_run_id": prepared.review_run_id, "result": invalid_pass},
                state_root=self.state_root,
            )

    def test_clean_residue_without_genesis_is_not_treated_as_first_creation(self) -> None:
        root = self._root()
        residue = root / f".{self.operation_key}.state.cafebabe.tmp"
        residue.write_bytes(b"residue")
        with self.assertRaisesRegex(review_state.ReviewStateError, "residue exists"):
            self.prepare()
        self.assertFalse(review_state._genesis_path(root, self.operation_key).exists())
        self.assertFalse(review_state._state_path(root, self.operation_key).exists())


if __name__ == "__main__":
    unittest.main()
