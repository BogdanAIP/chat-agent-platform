# Current State

## Snapshot

Architecture v1.4 is **Rust-first / native-edge**. Chat is primary intelligence; one local `agent-platform.exe` owns contracts, Project Binding, locked capability selection, policy, guarded confirmations, artifacts, persistent jobs and secret ACL. Mature tools and network components remain replaceable edge executors.

Python v0.1 is retained only as a behavioral oracle for parity. It is not the target runtime.

Repository is **public** and licensed under the standard **MIT License** with no additional mandatory conditions. Project support/donations are voluntary and separate from MIT rights.

The connector architecture is **provider-neutral**. There is no canonical Yandex/VPS/cloud transport. Canonical boundaries are standard MCP/compatibility contracts and the local security/execution boundary; hosting/tunnel/provider is chosen at deployment time. See `CONNECTOR_ARCHITECTURE.md` and ADR-009.

## Stage status

| Stage | Status | Current evidence |
| --- | --- | --- |
| 0 Reality baseline + Binding | done | Binding/GitHub proven; real Hosted Chat -> plugin -> Yandex -> Windows -> ChatGPT round trip passed 2026-08-06 |
| 1 Rust vertical core | done | binding -> policy -> artifact -> typed tool -> validated result |
| 2 Contracts | done | embedded schemas for tool/artifact/policy/confirmation/secret/job/relay |
| 3 Memory/bootstrap/skills | done | minimal project context + bootstrap path |
| 4 Hosted Chat -> local connector | done | real ChatGPT-originated local execution passed 2026-08-06; direct authenticated loopback ingress now has Windows process E2E; Yandex/polling relay remains fallback |
| 5 MCP aggregation | conditional | no extra aggregator justified; standard MCP should use official SDK, not a home-grown aggregator |
| 6 Capability selection + PEP | done | fail-closed quality/reliability/determinism/path/fallback/cost gates |
| 7 Secret Store | done | Windows Credential Manager + executor ACL |
| 8 Artifact hardening/staging | done | immutable SHA-verified inputs, recovery, controlled staging |
| 9 Supervisor/service | conditional | explicit ingress/relay lifecycle is sufficient |
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

On 2026-08-06 the installed ChatGPT integration `Music Video MCP Yandex Test` successfully returned a response from the local Windows agent:

- computer: `ID182019`;
- OS: Windows 11;
- agent: `0.2.1`;
- message: `Проверка локального агента`.

This proves:

```text
ChatGPT
  -> installed plugin/app tool
  -> remote HTTPS path
  -> local Windows agent
  -> local execution
  -> response back to ChatGPT
```

A later ChatGPT-originated `runtime_self_test` on 2026-08-09 reported `agent_offline` while the local agent was stopped. That is valid offline behavior and does not invalidate the successful 2026-08-06 round trip.

### Direct loopback ingress is now implemented and process-tested

`agent-platform.exe` now owns a direct compatibility ingress without a second service:

```text
HTTPS tunnel/proxy
  -> 127.0.0.1:8787/gpt
  -> X-MCP-Token authentication
  -> Project Binding + policy
  -> shared allowlisted local dispatch
```

Properties:

- binds only to `127.0.0.1`;
- foreground explicit lifecycle (`ingress configure-token`, `ingress serve`, `ingress remove-token`);
- caller secret is stored through the existing Windows Credential Manager-backed Secret Store;
- exact remote operation allowlist remains `local_ping`, `runtime_self_test`;
- authentication happens before dispatch;
- request body is bounded to 8 KiB;
- concurrency is bounded;
- direct ingress and polling relay share the same local operation dispatcher;
- `/gpt` + `X-MCP-Token` remain compatible with the existing action schema.

Windows Stage 4 E2E now proves the real process boundary:

1. unique caller token stored in Windows Credential Manager;
2. real `agent-platform.exe ingress serve` started on an ephemeral loopback port;
3. request without token returns `401`;
4. authenticated `local_ping` returns `200`, preserves the message and proves `executed_locally=true`;
5. process is stopped and the test credential is removed;
6. the existing polling-relay Credential Manager/lifecycle/Yandex contract regressions still pass.

This proves the local half of the preferred direct-tunnel path without adding another network service.

### Polling relay remains fallback

The provider-neutral Rust `relay-server` still passes dedicated round-trip/auth/failure CI and bounds SQLite retention during active traffic. The Yandex polling backend remains retained acceptance evidence and rollback infrastructure, not the target request path.

## Connector modernization

### Immediate live portability test

The next real network acceptance should reuse the currently working action contract and change only reachability:

```text
ChatGPT existing action/plugin
  -> mature public HTTPS tunnel
  -> 127.0.0.1:8787/gpt
  -> agent-platform auth + policy
  -> local_ping / runtime_self_test
```

Passing this proves that Yandex/VPS relay state is unnecessary for the current ChatGPT integration.

### Standard MCP remains the target protocol

After the direct-tunnel compatibility path is accepted, add standard MCP Streamable HTTP using the official Rust `rmcp` SDK behind the same local policy/dispatch core:

```text
MCP-capable caller
  -> HTTPS /mcp
  -> rmcp adapter
  -> agent-platform policy + typed local execution
```

Do not expand the hand-written compatibility MCP implementation.

### Secure MCP Tunnel is optional

OpenAI Secure MCP Tunnel is an optional private reachability adapter. It must not become a core dependency or prerequisite; public HTTPS/reverse tunnels and other mature deployment choices remain interchangeable.

### What still needs direct proof

Two migration/deprecation checks remain:

1. one real **non-Yandex ChatGPT -> mature HTTPS tunnel -> direct loopback ingress -> Windows -> ChatGPT** round trip;
2. native standard MCP `/mcp` acceptance on the user's actual ChatGPT surface after the `rmcp` adapter exists.

These do not reopen Stage 4; they determine when legacy Yandex/polling compatibility can be retired.

## Public CI / supply chain

Current enforced baseline:

- `ci / verify-windows` runs on every PR and every `main` push;
- active repository ruleset `main-protection` requires PR-based merging, strict up-to-date checks `verify-windows` + `gitleaks-history`, linear history, and blocks deletion/force-push with no bypass actors;
- Stage 4 Windows E2E now covers both the direct loopback ingress and the legacy polling fallback;
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

- run the real non-Yandex direct-tunnel acceptance against `/gpt`;
- implement standard local MCP Streamable HTTP using official `rmcp`;
- test public HTTPS `/mcp` from the user's actual ChatGPT surface;
- only then decide whether the legacy polling/GPT Action/Yandex deployment can be removed.

## Conditional/non-blocking follow-up

- MCP Apps UI for concrete interactive tools only;
- Secure MCP Tunnel only if private OpenAI reachability is useful and available;
- tunnel-specific recipes only for actual deployment paths; do not embed tunnel products into the core;
- real licensed/owned music corpus + human listening acceptance before subjective professional-quality claims;
- support/donation addresses when available;
- ArtifactStore unresolved-orphan operator cleanup when operational demand appears;
- Job/ConfirmationStore indexing/retention only after measured growth;
- Python oracle removal after a separate parity/stability gate;
- Stages 16–18 only from concrete product scenarios.

See `CONNECTOR_ARCHITECTURE.md`, `STAGE20_OPERATIONS.md`, `ROADMAP.md` and `KNOWN_ISSUES.md`.
