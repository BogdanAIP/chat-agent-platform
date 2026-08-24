from __future__ import annotations

import unittest

from runtime.control_plane.verification import (
    ExpectedEffect,
    FinishStatus,
    ObservationRef,
    ObservationSnapshot,
    StatePredicate,
    VerificationResult,
    VerificationStatus,
    evaluate_finish_gate,
    verify_expected_effect,
)


class Stage263BVerificationKernelTests(unittest.TestCase):
    @staticmethod
    def _ref(
        capability: str,
        subject: str,
        sequence: int,
        fingerprint: str,
        *,
        stream_id: str = "stream-main",
    ) -> ObservationRef:
        return ObservationRef(
            capability=capability,
            subject=subject,
            stream_id=stream_id,
            sequence=sequence,
            fingerprint=fingerprint,
        )

    @staticmethod
    def _result(effect_id: str, status: VerificationStatus) -> VerificationResult:
        return VerificationResult(
            effect_id=effect_id,
            status=status,
            reason=f"synthetic_{status.value}",
            observation=None,
        )

    def test_fresh_exact_effect_passes(self) -> None:
        before = self._ref("files", "artifact:result.txt", 7, "before")
        effect = ExpectedEffect(
            effect_id="file-created",
            before=before,
            predicates=(
                StatePredicate.equals("exists", expected=True),
                StatePredicate.equals("sha256", expected="abc123"),
                StatePredicate.equals("identity", "inode", expected=99),
            ),
        )
        after = ObservationSnapshot(
            ref=self._ref("files", "artifact:result.txt", 8, "after"),
            state={
                "exists": True,
                "sha256": "abc123",
                "identity": {"inode": 99, "device": 1},
            },
        )

        result = verify_expected_effect(effect, after)

        self.assertEqual(result.status, VerificationStatus.PASS)
        self.assertEqual(result.reason, "expected_effect_verified")
        self.assertTrue(all(item.status is VerificationStatus.PASS for item in result.predicate_results))

    def test_stale_reobservation_is_unknown_even_when_state_matches(self) -> None:
        before = self._ref("files", "artifact:result.txt", 7, "same")
        effect = ExpectedEffect(
            effect_id="freshness-required",
            before=before,
            predicates=(StatePredicate.equals("exists", expected=True),),
        )
        stale = ObservationSnapshot(ref=before, state={"exists": True})

        result = verify_expected_effect(effect, stale)

        self.assertEqual(result.status, VerificationStatus.UNKNOWN)
        self.assertEqual(result.reason, "stale_observation")

    def test_higher_sequence_from_another_stream_is_not_fresh_evidence(self) -> None:
        before = self._ref("files", "artifact:result.txt", 7, "before", stream_id="stream-a")
        effect = ExpectedEffect(
            effect_id="stream-bound",
            before=before,
            predicates=(StatePredicate.equals("exists", expected=True),),
        )
        other_stream = ObservationSnapshot(
            ref=self._ref(
                "files",
                "artifact:result.txt",
                999,
                "other",
                stream_id="stream-b",
            ),
            state={"exists": True},
        )

        result = verify_expected_effect(effect, other_stream)

        self.assertEqual(result.status, VerificationStatus.UNKNOWN)
        self.assertEqual(result.reason, "observation_stream_mismatch")

    def test_wrong_subject_or_capability_cannot_verify_effect(self) -> None:
        before = self._ref("browser", "page:primary", 1, "before")
        effect = ExpectedEffect(
            effect_id="navigated",
            before=before,
            predicates=(StatePredicate.equals("url", expected="https://example.com/done"),),
        )

        wrong_subject = ObservationSnapshot(
            ref=self._ref("browser", "page:other", 2, "after"),
            state={"url": "https://example.com/done"},
        )
        wrong_capability = ObservationSnapshot(
            ref=self._ref("windows", "page:primary", 2, "after"),
            state={"url": "https://example.com/done"},
        )

        self.assertEqual(verify_expected_effect(effect, wrong_subject).reason, "subject_mismatch")
        self.assertEqual(verify_expected_effect(effect, wrong_capability).reason, "capability_mismatch")

    def test_definite_mismatch_is_fail_and_incomplete_missing_evidence_is_unknown(self) -> None:
        before = self._ref("browser", "page:primary", 10, "before")
        effect = ExpectedEffect(
            effect_id="browser-result",
            before=before,
            predicates=(
                StatePredicate.equals("url", expected="https://example.com/result"),
                StatePredicate.equals("document", "title", expected="Result"),
            ),
        )

        mismatch = ObservationSnapshot(
            ref=self._ref("browser", "page:primary", 11, "mismatch"),
            state={"url": "https://example.com/wrong", "document": {"title": "Result"}},
        )
        incomplete = ObservationSnapshot(
            ref=self._ref("browser", "page:primary", 12, "incomplete"),
            state={"url": "https://example.com/result"},
            complete=False,
        )

        self.assertEqual(verify_expected_effect(effect, mismatch).status, VerificationStatus.FAIL)
        self.assertEqual(verify_expected_effect(effect, incomplete).status, VerificationStatus.UNKNOWN)

    def test_ambiguous_observation_is_unknown(self) -> None:
        before = self._ref("windows", "app:vscode", 3, "before")
        effect = ExpectedEffect(
            effect_id="window-focused",
            before=before,
            predicates=(StatePredicate.equals("window", "focused", expected=True),),
        )
        after = ObservationSnapshot(
            ref=self._ref("windows", "app:vscode", 4, "after"),
            state={"window": {"focused": True}},
            ambiguous=True,
        )

        result = verify_expected_effect(effect, after)

        self.assertEqual(result.status, VerificationStatus.UNKNOWN)
        self.assertEqual(result.reason, "ambiguous_observation")

    def test_same_kernel_handles_browser_and_windows_normalized_state(self) -> None:
        browser_before = self._ref("browser", "page:1", 1, "browser-before")
        browser_effect = ExpectedEffect(
            effect_id="browser-navigation",
            before=browser_before,
            predicates=(
                StatePredicate.equals("url", expected="https://example.com/json"),
                StatePredicate.equals("document", "title", expected="JSON"),
            ),
        )
        browser_after = ObservationSnapshot(
            ref=self._ref("browser", "page:1", 2, "browser-after"),
            state={"url": "https://example.com/json", "document": {"title": "JSON"}},
        )

        windows_before = self._ref("windows", "window:editor", 20, "windows-before")
        windows_effect = ExpectedEffect(
            effect_id="windows-identity",
            before=windows_before,
            predicates=(
                StatePredicate.equals("process", "pid", expected=1234),
                StatePredicate.equals("window", "hwnd", expected=5678),
                StatePredicate.equals("window", "focused", expected=True),
            ),
        )
        windows_after = ObservationSnapshot(
            ref=self._ref("windows", "window:editor", 21, "windows-after"),
            state={
                "process": {"pid": 1234},
                "window": {"hwnd": 5678, "focused": True},
            },
        )

        self.assertEqual(verify_expected_effect(browser_effect, browser_after).status, VerificationStatus.PASS)
        self.assertEqual(verify_expected_effect(windows_effect, windows_after).status, VerificationStatus.PASS)

    def test_finish_gate_requires_independent_goal_and_safety_evidence(self) -> None:
        passed_goal = self._result("goal", VerificationStatus.PASS)
        passed_safety = self._result("safety", VerificationStatus.PASS)

        done = evaluate_finish_gate(
            candidate_done=True,
            goal_results=(passed_goal,),
            safety_results=(passed_safety,),
        )
        missing_safety = evaluate_finish_gate(
            candidate_done=True,
            goal_results=(passed_goal,),
            safety_results=(),
        )

        self.assertEqual(done.status, FinishStatus.DONE)
        self.assertEqual(done.task_success, VerificationStatus.PASS)
        self.assertEqual(done.safety, VerificationStatus.PASS)
        self.assertEqual(missing_safety.status, FinishStatus.UNKNOWN)
        self.assertEqual(missing_safety.safety, VerificationStatus.UNKNOWN)

    def test_declared_optional_dimension_without_evidence_is_unknown(self) -> None:
        passed = self._result("pass", VerificationStatus.PASS)

        no_constraints_declared = evaluate_finish_gate(
            candidate_done=True,
            goal_results=(passed,),
            safety_results=(passed,),
            constraint_results=None,
        )
        constraints_declared_but_unverified = evaluate_finish_gate(
            candidate_done=True,
            goal_results=(passed,),
            safety_results=(passed,),
            constraint_results=(),
        )

        self.assertEqual(no_constraints_declared.constraints, VerificationStatus.PASS)
        self.assertEqual(no_constraints_declared.status, FinishStatus.DONE)
        self.assertEqual(
            constraints_declared_but_unverified.constraints,
            VerificationStatus.UNKNOWN,
        )
        self.assertEqual(constraints_declared_but_unverified.status, FinishStatus.UNKNOWN)

    def test_finish_gate_keeps_task_success_and_safety_separate(self) -> None:
        result = evaluate_finish_gate(
            candidate_done=True,
            goal_results=(self._result("goal", VerificationStatus.PASS),),
            safety_results=(self._result("safety", VerificationStatus.FAIL),),
        )

        self.assertEqual(result.status, FinishStatus.NOT_DONE)
        self.assertEqual(result.task_success, VerificationStatus.PASS)
        self.assertEqual(result.safety, VerificationStatus.FAIL)

    def test_candidate_done_never_self_authorizes_completion(self) -> None:
        passed = self._result("pass", VerificationStatus.PASS)
        result = evaluate_finish_gate(
            candidate_done=False,
            goal_results=(passed,),
            safety_results=(passed,),
        )

        self.assertEqual(result.status, FinishStatus.NOT_DONE)
        self.assertEqual(result.reason, "candidate_done_not_proposed")

    def test_unresolved_confirmation_blocks_done_without_rewriting_task_success(self) -> None:
        passed = self._result("pass", VerificationStatus.PASS)
        result = evaluate_finish_gate(
            candidate_done=True,
            goal_results=(passed,),
            safety_results=(passed,),
            unresolved=("user_confirmation_required",),
        )

        self.assertEqual(result.status, FinishStatus.UNKNOWN)
        self.assertEqual(result.reason, "unresolved_completion_requirement")
        self.assertEqual(result.task_success, VerificationStatus.PASS)
        self.assertEqual(result.safety, VerificationStatus.PASS)

    def test_observation_reference_requires_stream_identity(self) -> None:
        with self.assertRaises(ValueError):
            ObservationRef(
                capability="files",
                subject="artifact:x",
                stream_id="",
                sequence=1,
                fingerprint="fp",
            )


if __name__ == "__main__":
    unittest.main()
