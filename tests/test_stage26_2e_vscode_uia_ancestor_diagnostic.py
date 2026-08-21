from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "scripts" / "stage26-vscode-uia-ancestor-diagnostic.py"


class Stage262EVSCodeUIAAncestorDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = DIAGNOSTIC.read_text(encoding="utf-8")
        ast.parse(cls.source, filename=str(DIAGNOSTIC))

    def test_diagnostic_uses_isolated_ai_disabled_vscode_profile(self) -> None:
        for required in (
            '"--wait"',
            '"--new-window"',
            '"--disable-extensions"',
            '"--user-data-dir"',
            '"--extensions-dir"',
            '"--goto"',
            '"editor.accessibilitySupport": "on"',
            '"chat.disableAIFeatures": True',
            '"security.workspace.trust.enabled": False',
            "tempfile.gettempdir()",
            "QUALIFICATION_PREFIX",
            "shell=False",
        ):
            self.assertIn(required, self.source)

    def test_diagnostic_has_no_application_content_input_channel(self) -> None:
        forbidden = (
            "type_text_guarded",
            "arm_guarded_keyboard",
            "guarded_keyboard_frame",
            "require_foreground_hit_target",
            "SetForegroundWindow",
            "pyautogui",
            "pyperclip",
            "clipboard",
            "subprocess.run",
            "shell=True",
            "os.system",
            "act_guarded_coordinate",
            "press_guarded",
            "act_structural",
            "execute_windows",
        )
        for item in forbidden:
            with self.subTest(item=item):
                self.assertNotIn(item, self.source)
        self.assertIn('"keyboard_action_count": 0', self.source)
        self.assertIn('"pointer_action_count": 0', self.source)

    def test_focused_proxy_requires_exact_filename_textbox_identity(self) -> None:
        start = self.source.index("def _state_focused_proxy")
        end = self.source.index("\ndef _element_membership", start)
        helper = self.source[start:end]
        for required in (
            "state.focused_control",
            "item.observation_fingerprint == state.focused_control",
            'item.role.casefold() != "textbox"',
            "item.name.casefold() != unique_filename.casefold()",
            "item.enabled is not True",
            "item.focused is not True",
        ):
            self.assertIn(required, helper)
        self.assertNotIn("item.visible is not True", helper)
        self.assertNotIn("bounds.width", helper)

    def test_ancestor_chain_is_bounded_to_exact_window_subtree(self) -> None:
        start = self.source.index("def _focused_ancestor_chain")
        end = self.source.index("\ndef _chain_signature", start)
        helper = self.source[start:end]
        for required in (
            "resolver._find_target_windows(auto, window_title)",
            "expected_hwnd",
            "expected_pid",
            "TREE_SCOPE_DESCENDANTS",
            "MAX_WINDOW_CONTROL_SCAN",
            "client.GetFocusedElement()",
            "client.ControlViewWalker",
            "walker.GetParentElement(current)",
            "MAX_ANCESTOR_DEPTH",
            'membership == "outside_bound_window"',
            'membership == "bound_window"',
            "reached_bound_window",
        ):
            self.assertIn(required, helper)
        self.assertNotIn("GetRootElement", helper)
        self.assertNotIn("DesktopControl", helper)

    def test_every_tree_element_is_compareelements_bound(self) -> None:
        start = self.source.index("def _element_membership")
        end = self.source.index("\ndef _raw_element_mapping", start)
        helper = self.source[start:end]
        self.assertIn("client.CompareElements(root_element, element)", helper)
        self.assertIn("client.CompareElements(elements.GetElement(index), element)", helper)
        self.assertIn('return "outside_bound_window", None', helper)
        self.assertIn("multiple bound-window descendants", helper)

    def test_children_are_bounded_and_capped(self) -> None:
        start = self.source.index("def _child_summaries")
        end = self.source.index("\ndef _focused_ancestor_chain", start)
        helper = self.source[start:end]
        self.assertIn("MAX_CHILDREN_PER_ANCESTOR", helper)
        self.assertIn("walker.GetFirstChildElement(parent)", helper)
        self.assertIn("walker.GetNextSiblingElement(child)", helper)
        self.assertIn("_element_membership", helper)
        self.assertIn("ancestor child escaped exact bound-window subtree", helper)

    def test_only_known_transition_com_error_is_retryable(self) -> None:
        self.assertIn("TRANSIENT_COM_HRESULT = -2147220991", self.source)
        self.assertIn("def _is_transition_com_error", self.source)
        self.assertIn("if not _is_transition_com_error(exc):\n                    raise", self.source)

    def test_requires_three_stable_ancestor_chains(self) -> None:
        self.assertIn("CHAIN_STABLE_SAMPLES = 3", self.source)
        self.assertIn("signature == previous_signature", self.source)
        self.assertIn("stable_count += 1", self.source)
        self.assertIn("stable_count = 1", self.source)
        self.assertIn("stable_count >= CHAIN_STABLE_SAMPLES", self.source)
        self.assertIn("three stable focused Monaco ancestor chains", self.source)

    def test_cleanup_reuses_randomized_identity_revalidation(self) -> None:
        for required in (
            "driver._validated_cleanup_matches(",
            "expected_hwnd=bound_hwnd",
            "expected_pid=bound_pid",
            "expected_process_generation=process_generation",
            "driver._post_close",
            "driver._matching_vscode_windows(unique_filename)",
        ):
            self.assertIn(required, self.source)


if __name__ == "__main__":
    unittest.main()
