# Current State

## Snapshot

Architecture v1.4 is **Rust-first / native-edge**. Chat is primary intelligence; one local `agent-platform.exe` owns contracts, Project Binding, locked capability selection, policy, guarded confirmations, artifacts, persistent jobs and secret ACL. Mature tools and network components remain replaceable edge executors.

Python v0.1 is retained only as a behavioral oracle for parity. It is not the target runtime.

Repository is **public** and licensed under the standard **MIT License** with no additional mandatory conditions. Project support/donations are voluntary and separate from MIT rights.

The connector architecture is **provider-neutral**. There is no canonical Yandex/VPS/cloud transport. Canonical boundaries are standard MCP/relay contracts and the local security/execution boundary; hosting/tunnel/provider is chosen at deployment time. See `CONNECTOR_ARCHITECTURE.md` and ADR-009.

## Stage status

| Stage | Status | Current evidence |
| --- | --- | --- |
| 0 Reality baseline + Binding | done | Binding/GitHub proven; real Hosted Chat -> plugin -> Yandex -> Windows -> ChatGPT round trip passed 2026-08-06 |
| 1 Rust vertical core | done | binding -> policy -> artifact -> typed tool -> validated result |
| 2 Contracts | done | embedded schemas for tool/artifact/policy/confirmation/secret/job/relay |
| 3 Memory/bootstrap/skills | done | minimal project context + bootstrap path |
| 4 Hosted Chat -> local connector | done / legacy path accepted | real ChatGPT-originated local execution passed 2026-08-06; current Yandex backend -> Windows acceptance passed 2026-08-09; provider-neutral Rust relay-server has CI/integration acceptance |
| 5 MCP aggregation | conditional | no extra aggregator justified; standard MCP should use official SDK, not a home-grown aggregator |
| 6 Capability selection + PEP | done | fail-closed quality/reliability/determinism/path/fallback/cost gates |
| 7 Secret Store | done | Windows Credential Manager + executor ACL |
| 8 Artifact hardening/staging | done | immutable SHA-verified inputs, recovery, controlled staging |
| 9 Supervisor/service | conditional | current explicit connector lifecycle is sufficient |
| 10 CI + supply chain | done baseline | always-on Windows CI, active main ruleset, SHA-pinned Actions, secret/license/advisory/SBOM/CodeQL gates |
| 11 FFmpeg adapter | done | typed operations, EBU QC, duration-aware timeouts |
| 12 REAPER adapter | done | real user Windows acceptance passed 2026-08-08 |
| 13 Mastering analysis | done | profile-aware technical decision/safe-auto gate |
| 14 Persistent jobs | done | idempotency/checkpoints/retry + exclusive physical execution |
| 15 Technical mastering | done | immutable input snapshot + final QC + idempotent master |
| 16 Browser automation | conditional | no concrete scenario selected |
| 17 Video production | conditional | no concrete scenario selected |
| 18 Distribution | conditional | confirmation primitive done; external executors intentionally absent |
| 19 Reference mastering | done | real pinned Matchering engine + technical benchmark |
| 20 Operations audit | partial / release-gated | automated hardening complete; first versioned release remains the mandatory manual gate |

Stages are not a strict linear dependency chain. Connector modernization does not reopen a completed Hosted Chat transport gate.

## Core integrity guarantees

### Capability/config

`tools.yaml`, `tool-lock.yaml` and `capability-requirements.yaml` form one executable selection contract. Unknown fields fail closed. Selection enforces locked executor identity, enabled state, quality, reliability, determinism, execution path, fallback agreement and cost. Runtime profile is generated from the same locked selections and regression-tested against `tool-lock.yaml`.

### Artifacts/jobs

Workflow inputs are captured into immutable Artifact Store snapshots. The snapshot SHA-256 must match the policy/idempotency identity, so workflows process the exact bytes they authorized.

JobStore is file-backed, atomic and process-safe. Idempotent `begin` returns one job; a separate per-job OS lock guarantees one physical executor at a time. Crash/restart releases the OS lock while persisted checkpoint/job state remains resumable.

### Guarded external authority

PEP derives risk independently from model hints. ConfirmationStore binds exact project/capability/risk/action parameters, has bounded TTL, idempotent prepare without TTL extension, fresh policy re-evaluation, atomic one-shot consume and replay protection. A successful consume returns a non-clone `ConfirmationPermit`.

No publishing/distribution executor exists yet, so Stage 18 creates no external side effects.

## Media/audio

- FFmpeg: typed inspect/validate/lossless convert/PCM24 extract/two-pass loudness normalization/mux; no arbitrary command surface; short probe timeout plus duration-aware media timeout; quiet EBU frame logging with final summary preserved.
- REAPER: limited generated Lua/ReaScript; registered FFprobe-valid inputs; real Stage 12 user acceptance created and registered `.rpp` + 48 kHz WAV.
- Mastering: Stage 13 is the technical safe-auto gate; Stage 15 produces idempotent technical masters; Stage 19 invokes pinned Matchering 2.0.6 as a replaceable Python 3.10 edge process and then reuses Rust delivery QC.
- Stage 19 proves integration on a synthetic PCM24 benchmark. Subjective professional quality on a real musical corpus remains a separate quality-validation task.

## Stage 4 connector evidence

### Hosted Chat round trip is already proved

On 2026-08-06, after the user requested a repeated `local_ping`, the installed ChatGPT integration `Music Video MCP Yandex Test` successfully returned a response from the local Windows agent:

- computer: `ID182019`;
- OS: Windows 11;
- agent: `0.2.1`;
- message: `Проверка локального агента`;
- ChatGPT observed the full call completing in roughly ten seconds.

This is direct evidence for:

```text
ChatGPT
  -> installed plugin/app tool
  -> Yandex-hosted gateway
  -> local Windows agent
  -> local execution
  -> response back to ChatGPT
```

A later ChatGPT-originated `runtime_self_test` on 2026-08-09 reported `agent_offline` while the local agent was stopped. That is valid offline behavior and does not invalidate the successful 2026-08-06 round trip.

The current ChatGPT control plane also exposes the installed integration with app-specific `Allow all actions` permission, so this user's real integration is not read-only.

### Current polling backend evidence

The newer/current Yandex polling backend separately passed real Windows acceptance on 2026-08-09:

- `local_ping`: local execution proved;
- `runtime_self_test`: success;
- controlled write/read and cleanup: passed;
- relay returned to disabled state.

The provider-neutral Rust `relay-server` passes dedicated round-trip/auth/failure CI and bounds SQLite retention during active traffic.

Together these results close the original Hosted Chat -> local Stage 4 requirement. They do **not** make Yandex canonical.

## Connector modernization

### Canonical local target

```text
remote MCP caller
        |
        v
standard MCP /mcp
        |
        v
agent-platform local policy + typed execution
```

The local MCP implementation should migrate to official Rust `rmcp`. Project-owned code should implement policy/tool semantics, not another evolving MCP protocol stack.

### Public HTTPS first

Current OpenAI plugin developer documentation supports a normal public HTTPS Streamable HTTP MCP endpoint, typically `/mcp`, as a direct connection option. Therefore Secure MCP Tunnel is not a prerequisite.

The next acceptance should expose the `rmcp` server through one ordinary public HTTPS endpoint and attempt to add/call it from the user's real ChatGPT Work/plugin surface.

### Secure MCP Tunnel is optional

OpenAI Secure MCP Tunnel is useful when the MCP server should remain private. It is an OpenAI-specific outbound-only reachability adapter and requires separate Platform tunnel/runtime credentials. It should be tested only if private reachability is useful; it must not become a core dependency or be assumed to come with a ChatGPT subscription.

### Generic tunnels remain edge choices

If a public endpoint needs to reach a local loopback MCP server, use mature networking software such as frp/zrok-class tunnels or an ordinary VPS/reverse proxy. Do not implement NAT traversal, ACME/TLS automation or multiplexing in this project.

### What still needs direct proof

The historical Yandex plugin proves action-capable Hosted Chat integration but does not preserve enough connection metadata to prove that it used today's standard MCP Streamable HTTP `/mcp` path.

Therefore two **migration/portability** checks remain:

1. native standard MCP `/mcp` from the user's actual ChatGPT Work/plugin surface;
2. one real non-Yandex remote -> Windows round trip.

These checks are required before deprecating the Yandex/GPT Action-compatible path, not before calling Stage 4 complete.

## Public CI / supply chain

Current enforced baseline:

- `ci / verify-windows` runs on every PR and every `main` push;
- active repository ruleset `main-protection` requires PR-based merging, strict up-to-date checks `verify-windows` + `gitleaks-history`, linear history, and blocks deletion/force-push with no bypass actors;
- every `actions/checkout` uses an immutable SHA and `persist-credentials: false`;
- Rust 1.97.1 and hosted FFmpeg 9.0.0 are pinned;
- cargo-deny enforces dependency licenses, bans, sources and RustSec advisories;
- Gitleaks scans reachable git history with redaction;
- CodeQL scans Rust, Python and GitHub Actions;
- reproducible CycloneDX SBOM and Windows third-party notices are generated;
- weekly grouped Dependabot updates remain enabled.

## Release path

The tag-gated release path requires an existing exact `vX.Y.Z` reachable from `main` and validates Rust/Python/oracle version alignment from that exact tag.

A non-publishing Release Package E2E proves:

```text
Windows release binary
+ CycloneDX SBOM
+ MIT LICENSE
+ THIRD_PARTY_LICENSES.html
  -> exact-content ZIP
  -> SHA256SUMS self-check
```

The release workflow performs GitHub build-provenance attestation before publication and refuses to overwrite existing releases. The first actual `v0.2.0` tag/release has intentionally not been created yet.

## Manual gate remaining

1. Deliberately push the first `v0.2.0` tag and verify generated Release assets, checksums and provenance.

## Connector migration before legacy deprecation

- implement standard local MCP Streamable HTTP using official `rmcp`;
- test public HTTPS `/mcp` from the user's actual ChatGPT Work/plugin surface;
- prove one non-Yandex connector path;
- then decide whether the legacy Yandex/GPT Action-compatible deployment can be removed.

## Conditional/non-blocking follow-up

- MCP Apps UI for concrete interactive tools only;
- Secure MCP Tunnel only if private OpenAI reachability is useful and available;
- frp/zrok deployment recipes only for an actual deployment path; do not embed them into the core;
- real licensed/owned music corpus + human listening acceptance before subjective professional-quality claims;
- support/donation addresses when available;
- ArtifactStore unresolved-orphan operator cleanup when operational demand appears;
- Job/ConfirmationStore indexing/retention only after measured growth;
- Python oracle removal after a separate parity/stability gate;
- Stages 16–18 only from concrete product scenarios.

See `CONNECTOR_ARCHITECTURE.md`, `STAGE20_OPERATIONS.md`, `ROADMAP.md` and `KNOWN_ISSUES.md`.
