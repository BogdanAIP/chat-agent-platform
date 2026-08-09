#!/usr/bin/env bash
set -euo pipefail

release_tag="${1:?release tag is required}"
release_dir="${2:-runtime/release}"

cd "$release_dir"

for required in agent-platform.exe agent-platform.cdx.json LICENSE THIRD_PARTY_LICENSES.html; do
  test -s "$required" || {
    echo "Required release file is missing or empty: $required" >&2
    exit 1
  }
done

archive="agent-platform-${release_tag}-windows-x86_64.zip"
rm -f "$archive" SHA256SUMS

zip -9 "$archive" \
  agent-platform.exe \
  agent-platform.cdx.json \
  LICENSE \
  THIRD_PARTY_LICENSES.html

python - "$archive" <<'PY'
import sys
import zipfile

archive = sys.argv[1]
expected = {
    "agent-platform.exe",
    "agent-platform.cdx.json",
    "LICENSE",
    "THIRD_PARTY_LICENSES.html",
}
with zipfile.ZipFile(archive) as zf:
    names = set(zf.namelist())
if names != expected:
    raise SystemExit(f"unexpected release ZIP contents: {sorted(names)}")
PY

sha256sum \
  agent-platform.exe \
  agent-platform.cdx.json \
  LICENSE \
  THIRD_PARTY_LICENSES.html \
  "$archive" \
  > SHA256SUMS
sha256sum -c SHA256SUMS
