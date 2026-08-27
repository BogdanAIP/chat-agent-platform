import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RealTaskAcceptanceContractTests(unittest.TestCase):
    def test_real_task_contract_defines_three_evidence_levels(self):
        text = (ROOT / 'project-context' / 'REAL_TASK_ACCEPTANCE.md').read_text(encoding='utf-8')
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

    def test_roadmap_records_browser_then_windows_verifier_then_accepted_windows_l3(self):
        roadmap = (ROOT / 'project-context' / 'ROADMAP.md').read_text(encoding='utf-8')
        browser_l3 = roadmap.index('Browser L3 real-task acceptance')
        windows_verifier = roadmap.index('Windows DesktopState shared-kernel verification', browser_l3)
        windows_l3 = roadmap.index('Windows/application real-task L3', windows_verifier)
        self.assertLess(browser_l3, windows_verifier)
        self.assertLess(windows_verifier, windows_l3)
        self.assertIn('PHYSICAL ACCEPTED / MERGED #113', roadmap)
        self.assertIn('PHYSICAL ACCEPTED / MERGED #114', roadmap)
        self.assertIn('PHYSICAL ACCEPTED / MERGED #115', roadmap)
        self.assertIn('EXTERNAL_FINISH_GATE=DONE', roadmap)
        self.assertIn('repeat representative Browser L3 under stronger source-provenance methodology', roadmap)

    def test_roadmap_keeps_track_m_parallel_and_future(self):
        roadmap = (ROOT / 'project-context' / 'ROADMAP.md').read_text(encoding='utf-8')
        self.assertIn('Parallel Track M — Agent Sessions / Delegation / Conversation Bridge', roadmap)
        self.assertIn('HarnessSession', roadmap)
        self.assertIn('DelegationTask', roadmap)
        self.assertIn('MessageDelivery', roadmap)
        self.assertIn('ExecutionEnvironment', roadmap)
        self.assertIn('max_spawn_depth = 1', roadmap)
        self.assertIn('CapabilityRegistry', roadmap)
        self.assertIn('TypedEventBus', roadmap)
        self.assertIn('PolicyHooks', roadmap)

    def test_document_status_promotes_real_task_contract(self):
        status = (ROOT / 'project-context' / 'DOCUMENT_STATUS.md').read_text(encoding='utf-8')
        self.assertIn('`REAL_TASK_ACCEPTANCE.md` | AUTHORITATIVE ACCEPTANCE-DIRECTION CONTRACT', status)

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
        self.assertIn('exact source/runtime/dependency bytes are write/delete locked until Finish Gate cleanup', prepare)

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
