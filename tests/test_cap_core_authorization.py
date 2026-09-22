from __future__ import annotations

from dataclasses import replace
import unittest

from runtime.control_plane.authorization import (
    AuthorizationRequest,
    AuthorizationStatus,
    CapabilityGrant,
    authorize_request,
)


ATTEMPT_FINGERPRINT = "a" * 64


def grant(**overrides: object) -> CapabilityGrant:
    value: dict[str, object] = {
        "grant_ref": "grant:workspace:update:1",
        "task_ref": "task:core-auth-test",
        "principal_ref": "manager:ordinary-chatgpt",
        "capability": "workspace",
        "allowed_action_refs": ("artifact.create", "artifact.cleanup"),
        "resource_scope_ref": "workspace-root:fixture-a",
        "delegation_ref": None,
        "execution_environment_ref": "runtime:local-windows",
        "evidence_scope_ref": "workspace-stream:fixture-a",
    }
    value.update(overrides)
    return CapabilityGrant(**value)


def request(**overrides: object) -> AuthorizationRequest:
    value: dict[str, object] = {
        "task_ref": "task:core-auth-test",
        "principal_ref": "manager:ordinary-chatgpt",
        "capability": "workspace",
        "action_ref": "artifact.create",
        "resource_scope_ref": "workspace-root:fixture-a",
        "attempt_authorization_fingerprint": ATTEMPT_FINGERPRINT,
        "delegation_ref": None,
        "execution_environment_ref": "runtime:local-windows",
        "evidence_scope_ref": "workspace-stream:fixture-a",
    }
    value.update(overrides)
    return AuthorizationRequest(**value)


class CapCoreAuthorizationTests(unittest.TestCase):
    def test_exact_grant_match_authorizes_and_binds_exact_fingerprints(self) -> None:
        current_grant = grant()
        current_request = request()

        decision = authorize_request(current_request, current_grant)

        self.assertIs(decision.status, AuthorizationStatus.AUTHORIZED)
        self.assertTrue(decision.authorized)
        self.assertEqual("exact_grant_match", decision.reason)
        self.assertEqual(current_grant.grant_ref, decision.grant_ref)
        self.assertEqual(current_grant.fingerprint, decision.grant_fingerprint)
        self.assertEqual(current_request.fingerprint, decision.request_fingerprint)
        self.assertEqual(
            current_request.attempt_authorization_fingerprint,
            decision.attempt_authorization_fingerprint,
        )

    def test_missing_grant_is_blocked(self) -> None:
        decision = authorize_request(request(), None)

        self.assertIs(decision.status, AuthorizationStatus.BLOCKED)
        self.assertFalse(decision.authorized)
        self.assertEqual("grant_missing", decision.reason)
        self.assertIsNone(decision.grant_ref)
        self.assertIsNone(decision.grant_fingerprint)

    def test_every_exact_context_dimension_fails_closed_on_mismatch(self) -> None:
        cases = (
            ("task_ref", {"task_ref": "task:other"}, "task_ref_mismatch"),
            (
                "principal_ref",
                {"principal_ref": "worker:untrusted"},
                "principal_ref_mismatch",
            ),
            ("capability", {"capability": "browser"}, "capability_mismatch"),
            (
                "resource_scope_ref",
                {"resource_scope_ref": "workspace-root:other"},
                "resource_scope_ref_mismatch",
            ),
            (
                "delegation_ref",
                {"delegation_ref": "delegation:unexpected"},
                "delegation_ref_mismatch",
            ),
            (
                "execution_environment_ref",
                {"execution_environment_ref": "runtime:other"},
                "execution_environment_ref_mismatch",
            ),
            (
                "evidence_scope_ref",
                {"evidence_scope_ref": "workspace-stream:other"},
                "evidence_scope_ref_mismatch",
            ),
        )
        current_grant = grant()

        for label, overrides, reason in cases:
            with self.subTest(label=label):
                decision = authorize_request(request(**overrides), current_grant)
                self.assertIs(decision.status, AuthorizationStatus.BLOCKED)
                self.assertFalse(decision.authorized)
                self.assertEqual(reason, decision.reason)
                self.assertEqual(current_grant.grant_ref, decision.grant_ref)
                self.assertEqual(current_grant.fingerprint, decision.grant_fingerprint)

    def test_unlisted_action_is_blocked(self) -> None:
        decision = authorize_request(
            request(action_ref="artifact.delete-unrelated"),
            grant(),
        )

        self.assertIs(decision.status, AuthorizationStatus.BLOCKED)
        self.assertEqual("action_not_granted", decision.reason)

    def test_grant_fingerprint_is_canonical_over_action_order(self) -> None:
        first = grant(allowed_action_refs=("artifact.create", "artifact.cleanup"))
        second = grant(allowed_action_refs=("artifact.cleanup", "artifact.create"))

        self.assertEqual(first.allowed_action_refs, second.allowed_action_refs)
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_same_grant_ref_with_changed_scope_has_different_fingerprint(self) -> None:
        first = grant()
        changed = grant(resource_scope_ref="workspace-root:other")

        self.assertEqual(first.grant_ref, changed.grant_ref)
        self.assertNotEqual(first.fingerprint, changed.fingerprint)

    def test_request_fingerprint_binds_exact_attempt_and_action(self) -> None:
        baseline = request()
        changed_attempt = request(attempt_authorization_fingerprint="b" * 64)
        changed_action = request(action_ref="artifact.cleanup")

        self.assertNotEqual(baseline.fingerprint, changed_attempt.fingerprint)
        self.assertNotEqual(baseline.fingerprint, changed_action.fingerprint)

    def test_grant_rejects_duplicate_or_unbounded_action_sets(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not contain duplicates"):
            grant(allowed_action_refs=("artifact.create", "artifact.create"))

        with self.assertRaisesRegex(ValueError, "exceeds 64"):
            grant(
                allowed_action_refs=tuple(
                    f"action:{index}" for index in range(65)
                )
            )

    def test_request_requires_exact_sha256_attempt_fingerprint(self) -> None:
        for invalid in ("", "A" * 64, "a" * 63, "not-a-digest"):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
                    request(attempt_authorization_fingerprint=invalid)

    def test_optional_context_is_exact_not_wildcard(self) -> None:
        unrestricted_context_grant = grant(
            execution_environment_ref=None,
            evidence_scope_ref=None,
        )
        same = request(
            execution_environment_ref=None,
            evidence_scope_ref=None,
        )
        different = request(
            execution_environment_ref="runtime:local-windows",
            evidence_scope_ref=None,
        )

        self.assertTrue(authorize_request(same, unrestricted_context_grant).authorized)
        blocked = authorize_request(different, unrestricted_context_grant)
        self.assertFalse(blocked.authorized)
        self.assertEqual("execution_environment_ref_mismatch", blocked.reason)


if __name__ == "__main__":
    unittest.main()
