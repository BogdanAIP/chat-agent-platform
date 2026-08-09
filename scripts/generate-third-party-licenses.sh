#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output="${1:-$repo_root/runtime/release/THIRD_PARTY_LICENSES.html}"
version="0.9.1"
archive="cargo-about-${version}-x86_64-unknown-linux-musl.tar.gz"
expected_sha256="c0e7dc6f5d74b0beec5c0053d39ab24514c717d19acd91886907a22457ea9e98"
url="https://github.com/EmbarkStudios/cargo-about/releases/download/${version}/${archive}"
workdir="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/chat-agent-platform-cargo-about-${version}"

rm -rf "$workdir"
mkdir -p "$workdir/bin" "$(dirname "$output")"

curl --fail --location --proto '=https' --tlsv1.2 --output "$workdir/$archive" "$url"
echo "$expected_sha256  $workdir/$archive" | sha256sum --check --strict
tar -xzf "$workdir/$archive" -C "$workdir/bin" --strip-components=1
chmod +x "$workdir/bin/cargo-about"
"$workdir/bin/cargo-about" --version

cd "$repo_root"
"$workdir/bin/cargo-about" --color never generate \
  --manifest-path Cargo.toml \
  --workspace \
  --all-features \
  --locked \
  --fail \
  --config about.toml \
  --output-file "$output" \
  about.hbs

test -s "$output"
