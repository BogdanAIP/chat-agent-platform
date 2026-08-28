import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / 'project-context'


class RealTaskAcceptanceContractTests(unittest.TestCase):
    def test_real_task_contract_defines_three_evidence_levels(self):
        text = (CONTEXT / 'REAL_TASK_ACCEPTANCE.md').read_text(encoding='utf-8')
        folded = text.casefold()
        self.assertIn('l1 — primitive / contract', folded)
        self.assertIn('l2 — workflow / component integration', folded)
        self.assertIn('l3 — real user-task acceptance', folded)
        self.assertIn('does not provide a click/type script', folded)
        self.assertIn('independent final state', folded)
        self.assertIn('randomized run identity', folded)
        self.assertIn('non-target', folded)
        self.assertIn('independent evidence must not be planner-writable', folded)
        self.assertIn('external checker', folded)

    def test_stage26_3b_is_closed_in_roadmap_and_exact_l3_evidence_lives_in_index(self):
        roadmap = (CONTEXT / 'ROADMAP.md').read_text(encoding='utf-8')
        evidence = (CONTEXT / 'EVIDENCE_INDEX.md').read_text(encoding='utf-8')
        roadmap_folded = roadmap.casefold()

        self.assertIn('26.3b — verification kernel + independent finish gate — accepted / closed', roadmap_folded)
        self.assertIn('files, browser and windows/application paths', roadmap_folded)
        self.assertIn('headless playwright/chrome', roadmap_folded)

        for accepted_gate in (
            'Stage 26.3B Browser real-task L3 historical scope (#113)',
            'Stage 26.3B Windows DesktopState shared-kernel verification (#114)',
            'Stage 26.3B Windows/application real-task L3 (#115)',
            'Stage 26.3B Browser stronger source-provenance repeat (#118)',
        ):
            self.assertIn(accepted_gate, evidence)

        self.assertIn('EXTERNAL_FINISH_GATE=DONE', evidence)
        self.assertIn('SAVE_COUNT=1', evidence)
        self.assertIn('AUDIT_COUNT=1', evidence)

        # Exact accepted PR/evidence snapshots belong in EVIDENCE_INDEX, not the roadmap.
        self.assertNotIn('PHYSICAL ACCEPTED / MERGED #113', roadmap)
        self.assertNotIn('PHYSICAL ACCEPTED / MERGED #118', roadmap)

    def test_roadmap_keeps_track_m_parallel_and_future(self):
        roadmap = (CONTEXT / 'ROADMAP.md').read_text(encoding='utf-8')
        track_m = (CONTEXT / 'CONVERSATION_BRIDGE_ARCHITECTURE.md').read_text(encoding='utf-8')
        hooks = (CONTEXT / 'CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md').read_text(encoding='utf-8')
        combined = roadmap + track_m
        folded = roadmap.casefold()

        self.assertIn('parallel track m — agent sessions / delegation', folded)
        self.assertIn('future work-distribution capability', folded)
        self.assertIn('must not displace release-critical stage 26', folded)
        for identity in ('HarnessSession', 'DelegationTask', 'MessageDelivery', 'ExecutionEnvironment'):
            self.assertIn(identity, combined)
        self.assertIn('max_spawn_depth=1', roadmap)

        # Registry/event/hook detail is owned by ADR-037, not the roadmap.
        self.assertIn('CapabilityRegistry', hooks)
        self.assertIn('TypedEventBus', hooks)
        self.assertIn('PolicyHooks', hooks)

    def test_document_status_promotes_real_task_contract(self):
        status = (CONTEXT / 'DOCUMENT_STATUS.md').read_text(encoding='utf-8')
        row = next(line for line in status.splitlines() if '`REAL_TASK_ACCEPTANCE.md`' in line)
        folded = row.casefold()
        self.assertIn('authoritative', folded)
        self.assertIn('acceptance', folded)
        self.assertIn('l1/l2/l3', folded)

    def test_physical_preparation_isolates_fixture_evidence_from_chat_workspace(self):
        prepare = (ROOT / 'scripts' / 'prepare-browser-real-task-gate.ps1').read_text(encoding='utf-8')
        folded = prepare.casefold()
        self.assertIn("$workspaceroot = join-path $qualificationroot 'workspace'", folded)
        self.assertIn("$fixtureroot = join-path $qualificationroot 'fixture-state'", folded)
        self.assertIn('-filesroot $workspaceroot', folded)
        self.assertIn("join-path $workspaceroot 'stage26-3b-browser-real-task.txt'", folded)
        challenge_section = prepare[prepare.index('$challenge = @"'):prepare.index('$challengePath =', prepare.index('$challenge = @"'))]
        self.assertNotIn('FINISH_GATE_FILE', challenge_section)
        self.assertNotIn('SERVER_STATE_FILE', challenge_section)
        self.assertNotIn('AUDIT_FILE', challenge_section)
        self.assertIn('fixture/provenance/frozen-gate evidence is outside Chat workspace', prepare)
        self.assertIn('exact source/runtime/full Node dependency-tree bytes are write/delete locked until Finish Gate cleanup', prepare)

    def test_external_checker_requires_independent_state_and_target_only_history(self):
        checker = (ROOT / 'scripts' / 'check-browser-real-task-gate.ps1').read_text(encoding='utf-8')
        folded = checker.casefold()
        self.assertIn("'only_target_ever_mutated'", folded)
        self.assertIn("'decoys_unchanged'", folded)
        self.assertIn('fixture evidence must not live inside the chat workspace root', folded)
        self.assertIn('unexpected_mutation_set', folded)
        self.assertIn('frozen browser l3 audit mutation does not identify the single target save', folded)
        self.assertIn('frozen-snapshot.json', folded)
        self.assertIn('stage26_3b_browser_real_task_gate=pass', folded)


if __name__ == '__main__':
    unittest.main()
