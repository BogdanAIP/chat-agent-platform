from __future__ import annotations

from pathlib import Path
import unittest

from runtime.control_plane.windows_case_update import (
    PROCEDURE_ID,
    ProcedureAbstained,
    _replace_visible_lines,
    _settle_postcondition,
    _sha256_text,
    _state_token,
    _validate_request,
)


ROOT = Path(__file__).resolve().parents[1]
PROCEDURE = ROOT / "runtime" / "control_plane" / "windows_case_update.py"
CLI = ROOT / "runtime" / "control_plane" / "cli.py"
PROJECTION = ROOT / "runtime" / "semantic-projection" / "bin" / "semantic-control-plane-projection.mjs"
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"
BOOTSTRAP_WINDOWS = ROOT / "scripts" / "bootstrap-windows-procedure-runtime.ps1"
FIXTURE = ROOT / "scripts" / "stage26-windows-case-desk-fixture.ps1"
PREPARE = ROOT / "scripts" / "prepare-windows-case-l3.ps1"
CHECKER = ROOT / "scripts" / "check-windows-case-l3.ps1"
ATTESTATION = ROOT / "scripts" / "stage26-windows-runtime-attestation.py"


class WindowsApplicationL3Contracts(unittest.TestCase):
    def test_windows_case_request_is_bounded_and_session_bound(self) -> None:
        request = {
            "procedure": PROCEDURE_ID,
            "case_id": "CASE-12AB34CD-4821",
            "note": "Reviewed by ordinary Chat 12AB34CD",
            "status": "Approved",
        }
        self.assertEqual(
            _validate_request(request, run_id="12AB34CD"),
            (request["case_id"], request["note"], request["status"]),
        )

        with self.assertRaises(ProcedureAbstained):
            _validate_request(request, run_id="DEADBEEF")
        with self.assertRaises(ValueError):
            _validate_request({**request, "pid": 1234}, run_id="12AB34CD")
        with self.assertRaises(ValueError):
            _validate_request({**request, "status": "Closed"}, run_id="12AB34CD")
        with self.assertRaises(ValueError):
            _validate_request({**request, "note": "line1\nline2"}, run_id="12AB34CD")

    def test_visible_state_postconditions_are_exact_digest_inputs(self) -> None:
        empty_hash = _sha256_text("")
        before_token = _state_token(
            selected="NONE",
            status="NONE",
            note_sha256=empty_hash,
            saved=0,
        )
        after_token = _state_token(
            selected="CASE-12AB34CD-4821",
            status="NONE",
            note_sha256=empty_hash,
            saved=0,
        )
        before = "Heading\nCASESTATE|id=CASE-12AB34CD-4821|status=Pending|notes=1\n" + before_token
        after = _replace_visible_lines(before, {before_token: after_token})
        self.assertEqual(after.count(after_token), 1)
        self.assertNotIn(before_token, after)
        with self.assertRaises(ProcedureAbstained):
            _replace_visible_lines(before, {"missing": "replacement"})

    def test_postcondition_settle_uses_fresh_observations_without_repeating_action(self) -> None:
        observations = iter(({"sequence": 1}, {"sequence": 2}, {"sequence": 3}))
        statuses = iter(("fail", "unknown", "pass"))
        verified_sequences: list[int] = []

        def observe() -> dict[str, int]:
            return next(observations)

        def verify(after: dict[str, int]) -> dict[str, str]:
            verified_sequences.append(after["sequence"])
            return {"status": next(statuses)}

        after, result, metadata = _settle_postcondition(
            observe,
            verify,
            timeout_seconds=0.1,
            poll_seconds=0.001,
        )

        self.assertEqual(after, {"sequence": 3})
        self.assertEqual(result["status"], "pass")
        self.assertEqual(verified_sequences, [1, 2, 3])
        self.assertEqual(metadata["attempt_count"], 3)
        self.assertEqual(metadata["statuses"], ["fail", "unknown", "pass"])

    def test_postcondition_settle_never_synthesizes_pass_after_timeout(self) -> None:
        observe_count = 0

        def observe() -> dict[str, int]:
            nonlocal observe_count
            observe_count += 1
            return {"sequence": observe_count}

        def verify(_after: dict[str, int]) -> dict[str, str]:
            return {"status": "fail"}

        after, result, metadata = _settle_postcondition(
            observe,
            verify,
            timeout_seconds=0.0,
            poll_seconds=0.001,
        )

        self.assertEqual(after, {"sequence": 1})
        self.assertEqual(result["status"], "fail")
        self.assertEqual(observe_count, 1)
        self.assertEqual(metadata["attempt_count"], 1)
        self.assertEqual(metadata["statuses"], ["fail"])

    def test_procedure_uses_registered_windows_mechanics_and_cannot_claim_external_done(self) -> None:
        source = PROCEDURE.read_text(encoding="utf-8")
        self.assertIn('PROCEDURE_ID = "windows_case_update_v1"', source)
        self.assertIn('QUALIFICATION_ADMISSION = "stage26-3b-windows-l3"', source)
        self.assertIn('MAX_ACTIONS = 5', source)
        self.assertIn('POSTCONDITION_SETTLE_SECONDS = 2.0', source)
        self.assertIn('allow_legacy_exec=False', source)
        self.assertIn('WindowScopedUiaResolver()', source)
        self.assertIn('resolver.set_expected_process_id', source)
        self.assertIn('input_fn=bounded_input', source)
        self.assertIn('uia_fn=resolver.perform', source)
        self.assertIn('verify_windows_desktop_transition(', source)
        self.assertIn('outcome_verified', source)
        self.assertIn('"external_l3_finish_gate_required"', source)
        self.assertIn('external_finish_gate_required=True', source)
        self.assertIn('"bounded_execution_completed"', source)
        self.assertIn('"postcondition_observation"', source)
        self.assertEqual(source.count("_settle_postcondition("), 6)
        self.assertNotIn('fixture-state', source)
        self.assertNotIn('audit.jsonl', source)
        self.assertNotIn('state.json', source)
        self.assertNotIn('subprocess.', source)
        self.assertNotIn('shell=True', source)

        coordinate_section = source[
            source.index("def guarded_coordinate") : source.index("def guarded_type")
        ]
        type_section = source[
            source.index("def guarded_type") : source.index("initial = observe()")
        ]
        self.assertLess(
            coordinate_section.index("for _ in range(12)"),
            coordinate_section.index("resolve_unique(role, name)"),
        )
        self.assertLess(
            type_section.index("for _ in range(12)"),
            type_section.index("resolve_unique(role, name)"),
        )

        run_index = source.index("def run_windows_case_update")
        openadapt_index = source.index("from openadapt_flow", run_index)
        self.assertLess(run_index, openadapt_index)
        for transition_id in (
            '"select_case"',
            '"focus_note"',
            '"enter_note"',
            '"set_status"',
            '"save_case"',
        ):
            self.assertIn(transition_id, source)

    def test_cli_dispatch_is_explicit_not_generic(self) -> None:
        source = CLI.read_text(encoding="utf-8")
        self.assertIn("WORKSPACE_ARTIFACT_PROCEDURE_ID", source)
        self.assertIn("WINDOWS_CASE_PROCEDURE_ID", source)
        self.assertIn("run_verified_workspace_artifact", source)
        self.assertIn("run_windows_case_update", source)
        self.assertIn('raise ValueError("unknown or unregistered procedure")', source)
        for forbidden in ("importlib", "globals()[", "locals()[", "eval(", "exec("):
            self.assertNotIn(forbidden, source)

    def test_public_schema_exposes_only_user_level_windows_parameters(self) -> None:
        source = PROJECTION.read_text(encoding="utf-8")
        self.assertIn("const WINDOWS_CASE_PROCEDURE = 'windows_case_update_v1'", source)
        windows_schema = source[
            source.index("const windowsCaseProcedureSchema") :
            source.index("const server = new McpServer")
        ]
        for required in (
            "z.literal(WINDOWS_CASE_PROCEDURE)",
            "case_id",
            "note",
            "Approved",
            "Needs Review",
        ):
            self.assertIn(required, windows_schema)
        for forbidden in ("pid", "hwnd", "path", "backend", "command", "python"):
            self.assertNotIn(forbidden, windows_schema.casefold())
        self.assertIn("z.union([", source)
        self.assertEqual(source.count("server.registerTool("), 6)

    def test_fixture_mutates_case_records_only_on_save_and_keeps_audit(self) -> None:
        source = FIXTURE.read_text(encoding="utf-8")
        self.assertIn("Case Desk $RunId", source)
        self.assertIn("STATE|selected=", source)
        self.assertIn("CASESTATE|id=", source)
        self.assertIn("New case note", source)
        self.assertIn("Set status Approved", source)
        self.assertIn("Set status Needs Review", source)
        self.assertIn("Save case", source)
        self.assertIn("event = 'case_saved'", source)
        self.assertIn("$uiState = [pscustomobject]@{", source)
        self.assertEqual(source.count("$case.status = [string]$uiState.draft_status"), 1)
        self.assertEqual(source.count("$case.notes = @($case.notes)"), 1)
        self.assertNotIn("$selectedCaseId =", source)
        self.assertNotIn("$draftStatus =", source)
        self.assertNotIn("$saveCount =", source)
        save_handler = source[source.index("$saveButton.Add_Click") :]
        self.assertIn("Append-Utf8NoBom -Path $AuditPath", save_handler)
        before_save = source[: source.index("$saveButton.Add_Click")]
        self.assertNotIn("Append-Utf8NoBom -Path $AuditPath", before_save)

    def test_prepare_binds_source_installed_runtime_and_hides_finish_evidence_from_chat(self) -> None:
        source = PREPARE.read_text(encoding="utf-8")
        folded = source.casefold()
        self.assertIn("source-provenance-gate.py", folded)
        self.assertIn("installed-runtime-provenance.json", folded)
        self.assertIn("stage26-windows-runtime-attestation.py", folded)
        self.assertIn("openadapt_version_match", folded)
        self.assertIn("fixture-state", folded)
        self.assertIn("active-session.json", folded)
        self.assertIn("chat_app_rebind_required=true", folded)
        provenance_call = folded.index("& $sourcepython @provenanceargs")
        bootstrap_call = folded.index("-file $bootstrap")
        fixture_start = folded.index("$fixtureprocess = start-process")
        self.assertLess(provenance_call, bootstrap_call)
        self.assertLess(bootstrap_call, fixture_start)

        challenge_start = source.index('$challenge = @"')
        challenge_end = source.index('$challengePath =', challenge_start)
        challenge_section = source[challenge_start:challenge_end]
        for forbidden in (
            "fixture_root",
            "state_path",
            "audit_path",
            "active_session_path",
            "finish_gate_file",
            "windows_case_update_v1",
        ):
            self.assertNotIn(forbidden, challenge_section.casefold())

    def test_external_checker_requires_independent_state_history_and_cleanup(self) -> None:
        source = CHECKER.read_text(encoding="utf-8")
        folded = source.casefold()
        for required in (
            "source_provenance_pass",
            "installed_runtime_provenance_pass",
            "runtime_attestation_pass",
            "evidence_outside_chat_workspace",
            "target_final_state_pass",
            "decoys_unchanged",
            "only_target_ever_mutated",
            "audit_target_save_exactly_once",
            "audit_before_matches_seed",
            "audit_after_matches_final",
            "finish_gate = 'not_done'",
            "stage26_3b_windows_application_l3",
        ):
            self.assertIn(required, folded)
        self.assertIn("if ($done) { 'done' }", folded)
        self.assertIn("fixture_cleanup_pass", folded)
        self.assertIn("active_session_cleanup_pass", folded)

    def test_bootstrap_installs_windows_runtime_before_semantic_smoke(self) -> None:
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        windows = BOOTSTRAP_WINDOWS.read_text(encoding="utf-8")
        self.assertIn("bootstrap-windows-procedure-runtime.ps1", bootstrap)
        install_index = bootstrap.index("Install-ChatWindowsProcedureBundle")
        smoke_index = bootstrap.index("Invoke-ChatBootstrapSmokeTest")
        self.assertLess(install_index, smoke_index)
        for required in (
            "windows_observation.py",
            "windows_transition.py",
            "windows_case_update.py",
            "runtime\\windows\\actuation.py",
            "runtime\\windows\\observation.py",
            "runtime\\windows\\window_scoped_uia.py",
            "stage26-openadapt-lock.json",
        ):
            self.assertIn(required, windows)

    def test_runtime_attestation_binds_installed_openadapt_and_server_source(self) -> None:
        source = ATTESTATION.read_text(encoding="utf-8")
        self.assertIn('metadata.version("openadapt-flow")', source)
        self.assertIn("server = _upstream()", source)
        self.assertIn('"win_agent_server_sha256"', source)
        self.assertIn('"version_match"', source)
        self.assertIn("WINDOWS_RUNTIME_ATTESTATION_STATUS", source)


if __name__ == "__main__":
    unittest.main()
