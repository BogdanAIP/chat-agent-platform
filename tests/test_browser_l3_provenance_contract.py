import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts" / "prepare-browser-real-task-gate.ps1"
CHECKER = ROOT / "scripts" / "check-browser-real-task-gate.ps1"
GUARDIAN = ROOT / "scripts" / "stage26-browser-byte-lock-guardian.ps1"
FIXTURE = ROOT / "tests" / "fixtures" / "browser_real_task_server.mjs"


class BrowserL3ProvenanceContractTests(unittest.TestCase):
    def test_prepare_requires_explicit_exact_head_and_fresh_bootstrap(self):
        text = PREPARE.read_text(encoding="utf-8")
        folded = text.casefold()
        self.assertIn("[parameter(mandatory = $true)]", folded)
        self.assertIn("[validatepattern('^[0-9a-fa-f]{40}$')]", folded)
        self.assertNotIn("skipbootstrap", folded)
        self.assertNotIn("if (-not $expectedhead)", folded)
        self.assertIn("exact_head_mismatch", folded)
        self.assertIn("bootstrap-chat-platform failed", folded)

    def test_prepare_runs_clean_exact_head_source_provenance_before_runtime_and_fixture(self):
        text = PREPARE.read_text(encoding="utf-8")
        folded = text.casefold()
        provenance = folded.index("source provenance gate failed before browser l3 preparation")
        runtime = folded.index("-action start -nonotify")
        fixture = folded.index("start-process -filepath $node")
        self.assertLess(provenance, runtime)
        self.assertLess(provenance, fixture)
        self.assertIn("'--repo-root', $sourceroot", folded)
        self.assertIn("'--expected-head', $expectedhead", folded)
        self.assertIn("'--lockfile', 'runtime/semantic-projection/package-lock.json'", folded)
        self.assertIn("scripts/stage26-browser-byte-lock-guardian.ps1", folded)
        self.assertIn("scripts/semantic-projection-runtime.ps1", folded)
        self.assertIn("tests/fixtures/browser_real_task_server.mjs", folded)
        self.assertIn("-not [bool]$sourceprovenance.untracked_empty", folded)

    def test_prepare_binds_installed_semantic_runtime_helper(self):
        text = PREPARE.read_text(encoding="utf-8").casefold()
        mapping = "@('scripts\\semantic-projection-runtime.ps1', 'scripts\\semantic-projection-runtime.ps1')"
        self.assertIn(mapping, text)
        self.assertIn("foreach ($mapping in $installedmappings)", text)
        self.assertIn("foreach ($mapping in $installedmappings) { $lockpaths.add", text)

    def test_prepare_binds_complete_node_modules_tree_to_fresh_exact_lock(self):
        text = PREPARE.read_text(encoding="utf-8").casefold()
        self.assertIn("npm ci --ignore-scripts --no-audit --no-fund", text)
        self.assertIn("$installednodemodulesroot = join-path $installedpackageroot 'node_modules'", text)
        self.assertIn("$referencenodemodulesroot = join-path $dependencyreferenceroot 'node_modules'", text)
        self.assertIn("$lockpackagecount", text)
        self.assertIn(".chat-agent-platform-lock.sha256", text)
        self.assertIn("installed semantic runtime lock marker does not match the exact package-lock sha-256", text)
        self.assertIn("get-directorydigest -root $installednodemodulesroot -excluderelativepath", text)
        self.assertIn("get-directorydigest -root $referencenodemodulesroot -excluderelativepath", text)
        self.assertIn("installed semantic node dependency tree does not match fresh exact-lock npm-ci materialization", text)
        self.assertIn("scope = 'runtime/semantic-projection/node_modules'", text)
        self.assertIn("dependencies_match_exact_lock", text)
        self.assertNotIn("$dependencyrecords", text)
        self.assertNotIn("foreach ($packagename in @('@playwright/mcp'", text)

        # Guardian coverage must be whole-tree, not a package allowlist.
        self.assertIn("get-childitem -literalpath $installednodemodulesroot -recurse -file", text)
        self.assertIn("get-childitem -literalpath $referencenodemodulesroot -recurse -file", text)
        self.assertIn("node_runtime_exact_lock_materialization=pass", text)

    def test_byte_lock_guardian_hashes_through_held_no_write_delete_handles(self):
        text = GUARDIAN.read_text(encoding="utf-8").casefold()
        self.assertIn("[system.io.fileshare]::read", text)
        self.assertNotIn("[system.io.fileshare]::write", text)
        self.assertIn("get-streamsha256", text)
        self.assertIn("byte-lock target hash mismatch", text)
        self.assertIn("locked_file_count", text)
        self.assertIn("while (-not (test-path -literalpath $stoppath", text)

        prepare = PREPARE.read_text(encoding="utf-8").casefold()
        guardian_ready = prepare.index("browser byte-lock guardian did not become ready")
        runtime = prepare.index("-action start -nonotify")
        fixture = prepare.index("start-process -filepath $node")
        self.assertLess(guardian_ready, runtime)
        self.assertLess(guardian_ready, fixture)
        self.assertIn("byte_lock_guardian=pass", prepare)
        self.assertIn("semantic_transport_pid", prepare)

    def test_guardian_ready_handshake_uses_numeric_utc_ticks_not_datetime_string_parsing(self):
        guardian = GUARDIAN.read_text(encoding="utf-8").casefold()
        prepare = PREPARE.read_text(encoding="utf-8").casefold()
        self.assertIn("ready_time_ticks = $readyutc.ticks", guardian)
        self.assertIn("$guardianreadytimeticks = [long]$guardianready.ready_time_ticks", prepare)
        self.assertIn("[datetime]::new($guardianreadytimeticks, [datetimekind]::utc)", prepare)
        self.assertIn("guardian_ready_time_ticks = $guardianreadytimeticks", prepare)
        self.assertNotIn("[datetimeoffset]::parse([string]$guardianready.ready_at", prepare)

    def test_semantic_transport_generation_manifest_field_matches_checker(self):
        prepare = PREPARE.read_text(encoding="utf-8").casefold()
        checker = CHECKER.read_text(encoding="utf-8").casefold()
        self.assertIn(
            "semantic_transport_start_time_ticks = [long]$semantictransport.process_start_time_ticks",
            prepare,
        )
        self.assertIn("$manifest.semantic_transport_start_time_ticks", checker)
        self.assertNotIn("semantic_transport_process_start_time_ticks", prepare)
        self.assertNotIn("semantic_transport_process_start_time_ticks", checker)

    def test_fixture_exposes_authenticated_quiesce_and_atomic_snapshot(self):
        text = FIXTURE.read_text(encoding="utf-8").casefold()
        self.assertIn("--gate-token", text)
        self.assertIn("--generation", text)
        self.assertIn("/__gate/freeze", text)
        self.assertIn("x-gate-token", text)
        self.assertIn("writejsonatomic(snapshotpath", text)
        self.assertIn("if (frozen) return sendjson(response, 423", text)
        collect = text.index("const body = await collectbody(request)")
        recheck = text.index("if (frozen) return sendjson(response, 423", collect)
        mutation = text.index("cases[index] =", collect)
        self.assertLess(recheck, mutation)

    def test_checker_requires_exact_process_generations_and_atomic_freeze_before_evidence(self):
        text = CHECKER.read_text(encoding="utf-8")
        folded = text.casefold()
        self.assertIn("direct semantic transport process generation", folded)
        self.assertIn("browser byte-lock guardian generation", folded)
        self.assertIn("fixture process generation was not live", folded)
        freeze = folded.index("__gate/freeze")
        snapshot = folded.index("frozen-snapshot.json")
        finish = folded.index("finish_gate_not_done")
        self.assertLess(freeze, snapshot)
        self.assertLess(snapshot, finish)
        self.assertIn("atomic_final_snapshot=pass", folded)
        self.assertIn("semantic_transport_generation=pass", folded)

    def test_checker_revalidates_source_installed_helper_and_full_node_dependency_tree(self):
        text = CHECKER.read_text(encoding="utf-8").casefold()
        self.assertIn("browser l3 source provenance revalidation failed", text)
        self.assertIn("scripts/semantic-projection-runtime.ps1", text)
        self.assertIn("@('scripts\\semantic-projection-runtime.ps1', 'scripts\\semantic-projection-runtime.ps1')", text)
        self.assertIn("installed browser l3 runtime byte drift", text)
        self.assertIn("package-lock bytes drifted during run", text)
        self.assertIn("$dependencytree = $initialinstalled.dependency_tree", text)
        self.assertIn("runtime/semantic-projection/node_modules", text)
        self.assertIn("installed semantic runtime lock marker drifted from the exact package-lock sha-256", text)
        self.assertIn("installed full semantic node dependency-tree bytes drifted", text)
        self.assertIn("initial installed semantic node dependency tree was not identical to fresh exact-lock npm-ci materialization", text)
        self.assertIn("node_runtime_exact_lock_materialization=pass", text)
        self.assertIn("source_provenance_revalidated=pass", text)
        self.assertIn("installed_runtime_revalidated=pass", text)
        self.assertIn("provenance_revalidation=pass", text)
        self.assertNotIn("exact-lock record drifted for", text)
        self.assertNotIn("installed playwright dependency package bytes drifted", text)

    def test_checker_never_kills_reused_pid_and_emits_success_only_after_cleanup(self):
        text = CHECKER.read_text(encoding="utf-8")
        folded = text.casefold()
        self.assertIn("stop-verifiedprocesssafely", folded)
        self.assertNotIn("stop-process -id $fixturepid", folded)
        cleanup_gate = folded.index("if (-not $fixturecleanuppass)")
        pass_marker = folded.index("stage26_3b_browser_real_task_gate=pass")
        self.assertLess(cleanup_gate, pass_marker)
        self.assertIn("fixture_cleanup_pass=true", folded)
        self.assertIn("byte_lock_guardian_cleanup_pass=true", folded)

    def test_checker_requires_exactly_one_target_save_and_audit_mutation(self):
        text = CHECKER.read_text(encoding="utf-8").casefold()
        self.assertIn("requires exactly one persisted save", text)
        self.assertIn("requires exactly one audit mutation", text)
        self.assertIn("only_target_ever_mutated=true", text)
        self.assertIn("decoys_unchanged=true", text)
        self.assertIn("external_finish_gate=done", text)
        self.assertIn("non_target_mutation=none", text)


if __name__ == "__main__":
    unittest.main()
