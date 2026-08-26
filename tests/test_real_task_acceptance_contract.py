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

    def test_roadmap_requires_browser_l3_before_windows_verifier(self):
        roadmap = (ROOT / 'project-context' / 'ROADMAP.md').read_text(encoding='utf-8')
        browser_l3 = roadmap.index('Browser L3 real-task gate on replayed #112')
        windows_verifier = roadmap.index('Windows/application/process verification', browser_l3)
        self.assertLess(browser_l3, windows_verifier)

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
        self.assertIn('fixture-state is outside the Chat workspace', prepare)

    def test_external_checker_requires_independent_state_and_target_only_history(self):
        checker = (ROOT / 'scripts' / 'check-browser-real-task-gate.ps1').read_text(encoding='utf-8')
        folded = checker.casefold()
        self.assertIn("'only_target_ever_mutated'", folded)
        self.assertIn("'decoys_unchanged'", folded)
        self.assertIn('fixture evidence must not live inside the chat workspace root', folded)
        self.assertIn('unexpected_mutation_set', folded)
        self.assertIn('audit_wrong_target_mutation', folded)
        self.assertIn('stage26_3b_browser_real_task_gate=pass', folded)


if __name__ == '__main__':
    unittest.main()
