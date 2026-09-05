from __future__ import annotations

from pathlib import Path, PureWindowsPath


ROOT = Path(__file__).resolve().parents[1]
EXTENSION_ROOT = (
    ROOT
    / "runtime"
    / "agent_sessions"
    / "chatgpt_temporary_extension"
)

WINDOWS_CLASSIC_MAX_PATH = 260


def _longest_extension_relative_asset() -> Path:
    assets = [
        path.relative_to(EXTENSION_ROOT)
        for path in EXTENSION_ROOT.rglob("*")
        if path.is_file()
    ]
    if not assets:
        raise AssertionError("Temporary Chat extension has no files")

    return max(
        assets,
        key=lambda path: len(str(PureWindowsPath(*path.parts))),
    )


def projected_windows_qualification_asset(
    local_app_data: str | Path | PureWindowsPath,
    *,
    head: str = "a" * 40,
    task_sha256: str = "b" * 64,
) -> PureWindowsPath:
    operation_key = f"{head[:12]}-{task_sha256[:12]}"
    asset = _longest_extension_relative_asset()

    return (
        PureWindowsPath(str(local_app_data))
        / "ChatAgentPlatform"
        / "agent-sessions"
        / "qualification"
        / operation_key
        / f"exact-head-source-{head}"
        / "runtime"
        / "agent_sessions"
        / "chatgpt_temporary_extension"
        / PureWindowsPath(*asset.parts)
    )


def short_agent_session_localappdata(temp_root: str | Path) -> Path:
    root = Path(temp_root)
    projected = projected_windows_qualification_asset(root)

    if len(str(projected)) >= WINDOWS_CLASSIC_MAX_PATH:
        raise AssertionError(
            "WINDOWS_QUALIFICATION_PATH_BUDGET_EXCEEDED "
            f"length={len(str(projected))} "
            f"limit={WINDOWS_CLASSIC_MAX_PATH - 1} "
            f"path={projected}"
        )

    # TemporaryDirectory itself is already isolated.
    return root
