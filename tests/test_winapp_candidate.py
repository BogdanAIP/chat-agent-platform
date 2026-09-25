from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import runtime.windows.winapp_candidate as winapp_module
from runtime.windows.observation import Rect, build_desktop_state
from runtime.windows.routing import DesktopClickRequest, ObservedDesktopFrame, route_desktop_click
from runtime.windows.winapp_candidate import (
    WinAppCandidateRefused,
    WinAppDeliveryUnknown,
    WinAppInvokeCandidate,
)


def _state(*, generation: str = "process-start:123", name: str = "Save as",
           automation_id: str = "save-control"):
    return build_desktop_state(
        session_id="session:1", application_identity="sha256:fixture",
        executable_name="fixture.exe", process_id=1234,
        process_generation=generation, window_handle=5678, window_title="Fixture",
        window_bounds=Rect(100, 50, 600, 450),
        controls=[{
            "role": "button", "name": name, "automation_id": automation_id,
            "bounds": {"left": 140, "top": 110, "right": 260, "bottom": 170},
            "enabled": True, "visible": True, "focused": False,
        }],
        observed_at=datetime.now(timezone.utc).isoformat(),
    )


def _element(**changes):
    element = {
        "type": "Button", "name": "Save as", "automationId": "save-control",
        "selector": "save-control",
        "isEnabled": True, "isOffscreen": False, "isInvokable": True,
        "x": 140, "y": 110, "width": 120, "height": 60,
    }
    element.update(changes)
    return element


class _CLI:
    def __init__(self, *, status=None, search=None, invoke=None):
        self.commands = []
        self.status = status or {"processId": 1234, "processName": "fixture", "hwnd": 5678,
                                 "windowTitle": "Fixture"}
        self.search = search or {"matchCount": 1, "hasMore": False,
                                 "matches": [_element()]}
        self.invoke = invoke or {"elementId": "save-control", "pattern": "InvokePattern",
                                 "requestedAction": "invoke", "performedAction": "invoke",
                                 "hwnd": 5678}

    def __call__(self, args):
        self.commands.append(args)
        response = {"status": self.status, "search": self.search, "invoke": self.invoke}
        value = response[args[1]]
        if isinstance(value, Exception):
            raise value
        return value


class WinAppCandidateTests(unittest.TestCase):
    def setUp(self):
        self.state = _state()
        self.control = self.state.controls[0]
        self.request = DesktopClickRequest(
            window_name="Fixture", target_text="Save as", role="button",
            automation_id="save-control",
        )

    def candidate(self, cli, *, observe=None):
        return WinAppInvokeCandidate(
            binary=Path("/chosen/winapp.exe"),
            observe_window=observe or (lambda: _state()), run_cli=cli,
        )

    def test_route_delivers_one_exact_uia_operation_without_claiming_effect(self):
        cli = _CLI()
        states = [_state(), _state()]

        def observe(_screenshot):
            return ObservedDesktopFrame(states.pop(0))

        def forbidden(*_args):
            raise AssertionError("neither grounding nor coordinate click is authorized")

        routed = route_desktop_click(
            request=self.request, observe=observe, ground=forbidden,
            execute_structural=self.candidate(cli), execute_coordinate=forbidden,
        )
        self.assertEqual("delivered", routed.status)
        self.assertEqual("structural", routed.route)
        self.assertEqual("uia_invoke", routed.receipt["operation"])
        self.assertIs(routed.receipt["outcome_verified"], False)
        self.assertEqual([
            ("ui", "status", "-w", "5678", "--json"),
            ("ui", "search", "save-control", "-w", "5678", "--max", "50", "--json"),
            ("ui", "status", "-w", "5678", "--json"),
            ("ui", "invoke", "save-control", "-w", "5678", "--action", "invoke", "--json"),
        ], cli.commands)

    def test_app_control_without_automation_id_uses_unique_name_and_slug(self):
        state = _state(automation_id="")
        cli = _CLI(
            search={"matchCount": 1, "hasMore": False,
                    "matches": [_element(automationId=None, selector="btn-save-a123")]},
            invoke={"elementId": "btn-save-a123", "pattern": "InvokePattern",
                    "requestedAction": "invoke", "performedAction": "invoke", "hwnd": 5678},
        )
        candidate = self.candidate(cli, observe=lambda: _state(automation_id=""))
        receipt = candidate(replace(self.request, automation_id=None), state.controls[0], state)
        self.assertIs(receipt["outcome_verified"], False)
        self.assertEqual("Save as", cli.commands[1][2])
        self.assertEqual("btn-save-a123", cli.commands[-1][2])

    def test_wrong_window_or_process_refuses_before_action(self):
        for change in ({"processId": 9}, {"hwnd": 42}, {"processName": "decoy"},
                       {"windowTitle": "Other"}, {"processId": True}):
            with self.subTest(change=change):
                cli = _CLI(status={**_CLI().status, **change})
                with self.assertRaises(WinAppCandidateRefused):
                    self.candidate(cli)(self.request, self.control, self.state)
                self.assertEqual(["status"], [args[1] for args in cli.commands])

    def test_ambiguous_truncated_or_different_control_refuses(self):
        searches = [
            {"matchCount": 2, "hasMore": False, "matches": [_element(), _element()]},
            {"matchCount": 1, "hasMore": True, "matches": [_element()]},
            {"matchCount": 1, "hasMore": False,
             "matches": [_element(windowHandle=9999)]},
            {"matchCount": 1, "hasMore": False,
             "matches": [_element(type="Text")]},
            {"matchCount": 1, "hasMore": False,
             "matches": [_element(x=240)]},
            {"matchCount": 1, "hasMore": False,
             "matches": [_element(selector="--action")]},
        ]
        for search in searches:
            with self.subTest(search=search):
                cli = _CLI(search=search)
                with self.assertRaises(WinAppCandidateRefused):
                    self.candidate(cli)(self.request, self.control, self.state)
                self.assertEqual(["status", "search"], [args[1] for args in cli.commands])

    def test_generation_replacement_or_target_drift_refuses_after_search(self):
        for fresh in (_state(generation="different"), _state(name="Not the same control"),
                      self.state):
            with self.subTest(fresh=fresh):
                cli = _CLI()
                with self.assertRaises(WinAppCandidateRefused):
                    self.candidate(cli, observe=lambda: fresh)(
                        self.request, self.control, self.state)
                self.assertEqual(["status", "search"], [args[1] for args in cli.commands])

    def test_second_status_detects_window_swap_before_invoke(self):
        cli = _CLI()
        prior = cli.status
        seen = 0

        def run(args):
            nonlocal seen
            if args[1] == "status":
                seen += 1
                if seen == 2:
                    return {**prior, "processId": 4444}
            return cli(args)

        candidate = self.candidate(run)
        with self.assertRaises(WinAppCandidateRefused):
            candidate(self.request, self.control, self.state)
        self.assertEqual(["status", "search"], [args[1] for args in cli.commands])

    def test_stale_state_and_absent_role_refuse_without_cli(self):
        cli = _CLI()
        old = replace(self.state, observed_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat())
        with self.assertRaises(WinAppCandidateRefused):
            self.candidate(cli)(self.request, self.control, old)
        with self.assertRaises(WinAppCandidateRefused):
            self.candidate(cli)(replace(self.request, role=None), self.control, self.state)
        self.assertEqual([], cli.commands)

    def test_timeout_or_incomplete_reply_after_invoke_is_uncertain_without_retry(self):
        for outcome in (TimeoutError("after external effect"),
                        {"elementId": "wrong", "requestedAction": "invoke",
                         "performedAction": "invoke", "pattern": "InvokePattern", "hwnd": 5678}):
            with self.subTest(outcome=outcome):
                cli = _CLI(invoke=outcome)
                with self.assertRaises(WinAppDeliveryUnknown):
                    self.candidate(cli)(self.request, self.control, self.state)
                self.assertEqual(1, sum(args[1] == "invoke" for args in cli.commands))

    def test_explicit_binary_is_required(self):
        with self.assertRaises(ValueError):
            WinAppInvokeCandidate(binary=Path("winapp.exe"),
                                  observe_window=lambda: self.state, run_cli=_CLI())

    def test_real_transport_builds_bounded_no_shell_command(self):
        class _Binary:
            name = "winapp.exe"

            def resolve(self, *, strict):
                self.assert_true = strict
                return self

            def is_file(self):
                return True

            def __str__(self):
                return "C:\\Tools\\winapp.exe"

        binary = _Binary()
        output = SimpleNamespace(returncode=0, stdout='{"processId":1234}')
        with (
            patch.object(winapp_module, "os", SimpleNamespace(name="nt")),
            patch.object(winapp_module.subprocess, "CREATE_NO_WINDOW", 0, create=True),
            patch.object(winapp_module.subprocess, "run", return_value=output) as run,
        ):
            result = winapp_module._run_winapp_json(
                binary, ("ui", "status", "-w", "5678", "--json"))
        self.assertEqual(1234, result["processId"])
        self.assertIs(binary.assert_true, True)
        self.assertEqual(("C:\\Tools\\winapp.exe", "ui", "status", "-w", "5678", "--json"),
                         run.call_args.args[0])
        self.assertIs(run.call_args.kwargs["shell"], False)
        self.assertEqual(20, run.call_args.kwargs["timeout"])


if __name__ == "__main__":
    unittest.main()
