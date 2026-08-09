# Current State

## Snapshot

Architecture v1.4 is **Rust-first / native-edge**. Chat is primary intelligence; one local `agent-platform.exe` owns contracts, Project Binding, locked capability selection, policy, guarded confirmations, artifacts, persistent jobs and secret ACL. Mature tools and network components remain replaceable edge executors.

Python v0.1 is retained only as a behavioral oracle for parity. It is not the target runtime.

Repository is **public** and licensed under the standard **MIT License** with no additional mandatory conditions. Project support/donations are voluntary and separate from MIT rights.

The connector architecture is **provider-neutral**. There is no canonical Yandex/VPS/cloud transport. Canonical boundaries are the MCP/relay contracts and the local security/execution boundary; hosting/tunnel/provider is chosen at deployment time. See `CONNECTOR_ARCHITECTURE.md` and ADR-009.

## Stage status

| Stage | Status | Current evidence |
| --- | --- | --- |
| 0 Reality baseline + Binding | partial | Binding/GitHub proven; final Hosted Chat -> Windows call still pending through Stage 4 |
| 1 Rust vertical core | done | binding -> policy -> artifact -> typed tool -> validated result |
| 2 Contracts | done | embedded schemas for tool/artifact/policy/confirmation/secret/job/relay |
| 3 Memory/bootstrap/skills | done | minimal project context + bootstrap path |
| 4 Hosted Chat -> local connector | partial / one live backend accepted | local polling client is provider-neutral; real Yandex backend -> Windows acceptance passed 2026-08-09; Rust relay-server has CI/integration acceptance; final Hosted Chat-originated call and one live non-Yandex path remain |
| 5 MCP aggregation | conditional | no extra aggregator justified; standard MCP should use official SDK, not a home-grown aggregator |
| 6 Capability selection + PEP | done | fail-closed quality/reliability/determinism/path/fallback/cost gates |
| 7 Secret Store | done | Windows Credential Manager + executor ACL |
| 8 Artifact hardening/staging | done | immutable SHA-verified inputs, recovery, controlled staging |
| 9 Supervisor/service | conditional | current explicit relay lifecycle is sufficient |
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
| 20 Operations audit | partial / manual-gated | automated hardening complete; first release and final connector acceptance remain |

Stages are not a strict linear dependency chain. A later independent capability may be done while an earlier external/manual gate remains partial.

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

## Stage 4 connector architecture

### Canonical boundary

```text
Hosted Chat / Codex / other MCP client
        |
        | preferred: standard MCP Streamable HTTP
        | compatibility: GPT Action / polling relay
        v
replaceable public ingress
        |
        | direct HTTPS / reverse tunnel / VPS proxy / serverless relay
        v
local MCP boundary or outbound polling worker
        |
        v
agent-platform.exe -> policy -> typed local capability
```

The provider is not part of the capability contract.

### Existing provider-neutral polling client

The Windows runtime already stores only:

```text
endpoint
secret_ref
```

It accepts a normal HTTPS endpoint and sends the same authenticated JSON `poll/result/offline` protocol. Therefore changing the compatible server from Yandex to the Rust relay-server or another implementation requires configuration, not changes to local capability code.

Current polling backends:

- `crates/relay-server` — provider-neutral Rust implementation for an ordinary Linux host, with SQLite short-lived state and bounded retention;
- Yandex API Gateway / Function / Object Storage — provider-specific tested implementation retained as an adapter/reference.

### Preferred MCP direction

For MCP-capable callers the target is standard MCP Streamable HTTP. Protocol implementation should migrate to the official Rust MCP SDK (`rmcp`) in a separate change set rather than extending the hand-written compatibility implementation in `relay-server`.

When an outbound reverse tunnel can publish a local MCP endpoint, no custom polling relay is required. Mature tunnel/reverse-proxy software should be used instead of reimplementing NAT traversal. The architecture records frp as the self-hosted VPS reference and zrok as an optional managed/self-hosted zero-trust alternative; equivalent mature deployment choices remain allowed.

### GPT Action compatibility

The existing private GPT Action/OpenAPI surface remains useful where that is the available ChatGPT integration. Its HTTPS target is replaceable. The Yandex API Gateway requirement was specific to the tested Yandex adapter's handling of the incoming Authorization header and is not a platform invariant.

### Stage 4 evidence

Already proved:

- hosted CI for explicit configure/start/status/stop, token separation, Credential Manager storage, exact remote allowlist (`local_ping`, `runtime_self_test`), immutable task/result semantics, lost-ACK retry and offline lifecycle;
- real Yandex polling-backend -> Windows acceptance on 2026-08-09:
  - `local_ping`: `pong=true`, `executed_locally=true`;
  - `runtime_self_test`: success;
  - controlled write/read and cleanup: passed;
  - relay returned to disabled state;
- provider-neutral Rust relay-server integration/CI round trip;
- relay-server long-running SQLite retention is bounded during active traffic.

Still required before provider portability is considered fully proved:

1. a request originated by Hosted Chat through the chosen supported ingress and returned from real local execution;
2. one real non-Yandex remote -> Windows path using either the Rust polling relay or standard tunneled MCP.

Until the Hosted Chat gate passes, higher-value local media/mastering/distribution capabilities are not exposed remotely.

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

## Manual gates remaining

1. Complete real Hosted Chat -> local Windows -> Hosted Chat Stage 4 acceptance using a supported ingress.
2. Prove one real non-Yandex connector path to demonstrate deployment portability rather than only code-level portability.
3. Deliberately push the first `v0.2.0` tag and verify generated Release assets, checksums and provenance.

## Conditional/non-blocking follow-up

- migrate standard MCP ingress to `rmcp` and test MCP 2026-07-28 compatibility;
- add thin frp/zrok deployment recipes only when running the real second connector acceptance; do not embed either tunnel into the core;
- real licensed/owned music corpus + human listening acceptance before subjective professional-quality claims;
- support/donation addresses when available;
- ArtifactStore unresolved-orphan operator cleanup when operational demand appears;
- Job/ConfirmationStore indexing/retention only after measured growth;
- Python oracle removal after a separate parity/stability gate;
- Stages 16–18 only from concrete product scenarios.

See `CONNECTOR_ARCHITECTURE.md`, `STAGE20_OPERATIONS.md`, `ROADMAP.md` and `KNOWN_ISSUES.md`.
