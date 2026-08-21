from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from typing import Any


BASE_DIAGNOSTIC = Path(__file__).with_name("stage26-vscode-uia-ancestor-diagnostic.py")
ANCESTOR_RETRY_LIMIT = 8
ANCESTOR_RETRY_INTERVAL_SECONDS = 0.25
TRANSIENT_ANCESTOR_HRESULTS = {
    -2147220991,  # Chromium accessibility provider transition.
    -2147467261,  # E_POINTER: stale UIA element during provider tree rebuild.
}


def _load_base() -> Any:
    spec = importlib.util.spec_from_file_location(
        "stage26_vscode_uia_ancestor_diagnostic_base",
        BASE_DIAGNOSTIC,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load base diagnostic: {BASE_DIAGNOSTIC}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _is_transient_ancestor_com_error(exc: BaseException) -> bool:
    return type(exc).__name__ == "COMError" and bool(
        getattr(exc, "args", ()) and exc.args[0] in TRANSIENT_ANCESTOR_HRESULTS
    )


def main() -> int:
    base = _load_base()
    original = base._focused_ancestor_chain
    retry_events: list[dict[str, object]] = []

    def resilient_focused_ancestor_chain(*args: Any, **kwargs: Any) -> Any:
        last_exc: BaseException | None = None
        for retry in range(ANCESTOR_RETRY_LIMIT + 1):
            try:
                return original(*args, **kwargs)
            except Exception as exc:
                if not _is_transient_ancestor_com_error(exc):
                    raise
                last_exc = exc
                retry_events.append(
                    {
                        "retry": retry + 1,
                        "hresult": exc.args[0],
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                if retry >= ANCESTOR_RETRY_LIMIT:
                    break
                time.sleep(ANCESTOR_RETRY_INTERVAL_SECONDS)
        assert last_exc is not None
        raise last_exc

    base._focused_ancestor_chain = resilient_focused_ancestor_chain
    exit_code = int(base.main())

    print(f"ANCESTOR_INNER_RETRY_COUNT={len(retry_events)}")
    print(f"ANCESTOR_INNER_RETRIES={retry_events}")
    print(f"ANCESTOR_V2_EXIT_CODE={exit_code}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
