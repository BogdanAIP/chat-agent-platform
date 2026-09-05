from __future__ import annotations

import ast
from pathlib import Path, PureWindowsPath
import unittest

from tests.agent_session_test_paths import (
    WINDOWS_CLASSIC_MAX_PATH,
    projected_windows_qualification_asset,
)


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "tests"


def _launcher_localappdata_test_files() -> list[Path]:
    return [
        path
        for path in sorted(TEST_ROOT.glob("test_chatgpt_temporary*.py"))
        if "launch-chatgpt-temporary-worker.ps1" in path.read_text(encoding="utf-8")
        and "LOCALAPPDATA" in path.read_text(encoding="utf-8")
    ]


def _nested_localappdata_lines(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[int] = []

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Div)
            and isinstance(node.right, ast.Constant)
            and node.right.value == "localappdata"
        ):
            hits.append(node.lineno)

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "joinpath"
            and any(
                isinstance(arg, ast.Constant)
                and arg.value == "localappdata"
                for arg in node.args
            )
        ):
            hits.append(node.lineno)

    return sorted(set(hits))


class AgentSessionFailureClassGuardTests(unittest.TestCase):
    def test_launcher_localappdata_tests_use_shared_path_budget_helper(self) -> None:
        files = _launcher_localappdata_test_files()
        self.assertGreaterEqual(len(files), 4)

        offenders = [
            path.name
            for path in files
            if "short_agent_session_localappdata(" not in path.read_text(encoding="utf-8")
        ]
        self.assertEqual([], offenders)

    def test_launcher_tests_do_not_reintroduce_nested_localappdata(self) -> None:
        offenders: list[str] = []
        for path in _launcher_localappdata_test_files():
            for lineno in _nested_localappdata_lines(path):
                offenders.append(f"{path.name}:{lineno}")
        self.assertEqual([], offenders)

    def test_extra_localappdata_level_crosses_classic_windows_budget(self) -> None:
        representative_temp = PureWindowsPath(
            r"C:\Users\developer\AppData\Local\Temp\tmp12345678"
        )
        direct = projected_windows_qualification_asset(representative_temp)
        nested = projected_windows_qualification_asset(
            representative_temp / "localappdata"
        )

        self.assertLess(len(str(direct)), WINDOWS_CLASSIC_MAX_PATH, str(direct))
        self.assertGreaterEqual(
            len(str(nested)),
            WINDOWS_CLASSIC_MAX_PATH,
            str(nested),
        )


if __name__ == "__main__":
    unittest.main()
