from __future__ import annotations

import argparse
import hashlib
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.windows.window_scoped_uia import _upstream  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    lock_path = Path(args.lock).resolve()
    output_path = Path(args.output).resolve()
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": "fail",
        "lockfile": str(lock_path),
        "lockfile_sha256": None,
        "repository": None,
        "expected_commit": None,
        "expected_version": None,
        "installed_version": None,
        "version_match": False,
        "win_agent_server_path": None,
        "win_agent_server_sha256": None,
        "error": None,
    }
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
        flow = lock["upstreams"]["openadapt_flow"]
        expected_version = str(flow["declared_version"])
        installed_version = metadata.version("openadapt-flow")
        server = _upstream()
        server_file_raw = getattr(server, "__file__", None)
        if not server_file_raw:
            raise RuntimeError("OpenAdapt win_agent server module has no source path")
        server_path = Path(server_file_raw).resolve()
        if not server_path.is_file():
            raise RuntimeError(f"OpenAdapt win_agent server source is missing: {server_path}")

        result.update(
            {
                "lockfile_sha256": _sha256(lock_path),
                "repository": str(flow["repository"]),
                "expected_commit": str(flow["commit"]),
                "expected_version": expected_version,
                "installed_version": installed_version,
                "version_match": installed_version == expected_version,
                "win_agent_server_path": str(server_path),
                "win_agent_server_sha256": _sha256(server_path),
            }
        )
        result["status"] = "pass" if result["version_match"] else "fail"
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"WINDOWS_RUNTIME_ATTESTATION={output_path}")
    print(f"OPENADAPT_EXPECTED_VERSION={result['expected_version']}")
    print(f"OPENADAPT_INSTALLED_VERSION={result['installed_version']}")
    print(f"OPENADAPT_VERSION_MATCH={result['version_match']}")
    print(f"OPENADAPT_WIN_AGENT_SERVER_SHA256={result['win_agent_server_sha256']}")
    print(f"WINDOWS_RUNTIME_ATTESTATION_STATUS={result['status'].upper()}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
