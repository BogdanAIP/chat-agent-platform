# Current State

## Snapshot

Architecture v1.4 is **Rust-first / native-edge**. Chat is primary intelligence; one local `agent-platform.exe` owns contracts, Project Binding, locked capability selection, policy, guarded confirmations, artifacts, persistent jobs and secret ACL. Mature media tools remain typed edge executors.

Python v0.1 is retained only as a behavioral oracle for parity. It is not the target runtime.

Repository is private. `LicenseRef-UNLICENSED` means no project license has been selected yet.

**Current infrastructure blocker:** GitHub hosted Actions no longer starts private-repository jobs because the account spending/payment limit has been reached. GitHub returns the blocker before checkout or any project step. The user pre-authorized converting the repository to public if this exact condition blocks development, but the GitHub connector exposed to this Chat session has no repository-visibility mutation, so private -> public currently requires a manual GitHub UI/admin action. Code PRs requiring CI must remain unmerged until runner access is restored.

## Stage status

| Stage | Status | Current evidence |
| --- | --- | --- |
| 0 Reality baseline + Binding | partial | Binding/GitHub proven; real Hosted Chat -> Windows round trip still deferred |
| 1 Rust vertical core | done | binding -> policy -> artifact -> FFmpeg -> validated tool result |
| 2 Contracts | done | embedded schemas for tool/artifact/policy/confirmation/secret/job/relay |
| 3 Memory/bootstrap/skills | done | minimal project context + bootstrap path |
| 4 Hosted transport | partial / E2E-ready | Yandex relay hosted Windows E2E green; final real ChatGPT call pending |
| 5 MCP aggregation | conditional | no extra aggregator justified |
| 6 Capability selection + PEP | done | strict fail-closed quality/reliability/determinism/path/fallback/cost gates |
| 7 Secret Store | done | Windows Credential Manager + executor ACL |
| 8 Artifact hardening/staging | done | SHA/recovery/staging controls |
| 9 Supervisor/service | conditional | not required by current manual lifecycle |
| 10 CI baseline | done but runner access blocked | Windows verify/path filters/caches/pinned tools + supply-chain gates were green before spending-limit block |
| 11 FFmpeg adapter | done | typed media operations, EBU QC, duration-aware timeouts |
| 12 REAPER adapter | done | real user Windows acceptance passed 2026-08-08 |
| 13 Mastering analysis | done | profile-aware technical decision/safe-auto gate |
| 14 Persistent jobs | done | idempotency/checkpoints/retry + exclusive physical execution |
| 15 Technical mastering | done | immutable input snapshot + final QC + idempotent master |
| 16 Browser automation | conditional | no concrete scenario selected |
| 17 Video production | conditional | no concrete scenario selected |
| 18 Distribution | conditional | confirmation primitive done; external executors intentionally absent |
| 19 Reference mastering | done | real pinned Matchering engine + technical benchmark |
| 20 Operations audit | partial | hardening/release packaging done; manual gates + current runner-access blocker remain |

Stages are **not a strict linear dependency chain**. A later independent local capability may be completed while an earlier external/manual gate remains partial. A stage is `done` only for its own exit criteria.

## Core integrity guarantees

### Capability configuration

`tools.yaml`, `tool-lock.yaml` and `capability-requirements.yaml` form one executable selection contract. Unknown fields fail closed. Selection enforces:

- locked executor identity and enabled state;
- required quality;
- required reliability;
- required determinism;
- allowed execution path;
- exact fallback agreement;
- request cost limit.

QC/skills/acceptance lists are evidence metadata proved by tests or health. Runtime profile is generated from the locked selection set and regression-tested against `tool-lock.yaml`.

### Artifacts and jobs

Workflow inputs are captured into immutable Artifact Store snapshots before processing. The snapshot SHA-256 must match the policy/idempotency identity. Workflows process the registered snapshot rather than reopening an untrusted original path.

JobStore is file-backed, atomic and process-safe. Idempotent `begin` returns one job; a separate per-job OS lock guarantees one physical executor at a time. Crash/restart releases the OS lock while persisted checkpoint/job state remains resumable.

### Guarded external authority

PEP still derives risk independently from model hints. Guarded actions additionally have a stable `confirmation_binding`.

ConfirmationStore provides:

- 30–900 second TTL, default 10 minutes;
- idempotent prepare for the same active action;
- retry cannot extend an existing TTL;
- fresh policy re-evaluation before consume;
- exact project/capability/risk/binding check;
- atomic one-shot consume and replay protection;
- non-clone `ConfirmationPermit` for a future external executor.

No publishing/distribution executor exists yet, so Stage 18 does not create external side effects.

## Media/audio

### FFmpeg

Typed operations: inspect, validate, lossless convert, PCM24 extract, two-pass loudness normalization and mux. Arbitrary shell/FFmpeg args are not exposed.

Short probes use a separate short timeout. Media processing budget scales with validated input duration with a floor and hard ceiling. EBU inspection suppresses per-frame loudness logs while preserving the final Summary used by the parser, preventing stderr growth proportional to long media duration.

### REAPER

Rust generates a limited Lua/ReaScript driver. Inputs must be registered FFprobe-valid audio artifacts. Forbidden execution primitives are rejected. Real Stage 12 acceptance created and registered `.rpp` + 48 kHz WAV on the user's installed REAPER.

### Mastering

Stage 13 is the authoritative technical safe-auto decision gate. Stage 15 produces idempotent technical delivery masters. Stage 19 adds reference-based mastering through pinned Matchering 2.0.6 as a replaceable Python 3.10 edge runtime and then reuses Rust delivery QC.

Stage 19 proves technical integration on a synthetic PCM24 benchmark, not subjective professional quality on a real musical corpus.

## Stage 4 transport

Implemented shape:

```text
ChatGPT MCP / private GPT Action
        |
        v
Yandex Cloud Function
        |
        v
Object Storage task/result/heartbeat JSON
        ^
        | outbound HTTPS long poll
        |
agent-platform.exe on Windows
```

Properties already proved in hosted CI before the current account-level Actions block:

- relay off by default, explicit configure/start/status/stop;
- independent `AGENT_TOKEN` and remote bearer;
- local token in Credential Manager;
- exact two-operation remote allowlist: `local_ping`, `runtime_self_test`;
- immutable task/result rendezvous;
- cached response retry after lost acknowledgement without local re-execution;
- minimal unauthenticated health;
- stop -> cloud offline lifecycle.

Final real ChatGPT-originated round trip is intentionally deferred. Until it is completed, higher-value local capabilities remain unavailable through the remote surface.

## Supply chain / release operations

Current automated controls, last proven green before the account-level Actions block:

- Rust 1.97.1 pinned in CI;
- hosted FFmpeg 9.0.0 pinned;
- `cargo-deny` bans/sources;
- blocking RustSec advisories on dependency-changing PR/push;
- pinned reproducible CycloneDX SBOM generation;
- grouped weekly Dependabot updates;
- CI caches and path filters;
- Rust workspace, Python package and Python oracle versions regression-tested for equality;
- tag-gated release workflow requires an existing exact `vX.Y.Z` reachable from `main`;
- release build uses locked dependencies and packages Windows binary + SBOM + verified `SHA256SUMS`;
- existing GitHub Release assets are treated as immutable and never overwritten by the workflow.

The first real tag/release has intentionally not been created. GitHub artifact attestation is not enabled while the private repository lacks the required entitlement.

## Active unmerged work held for CI

- PR #25 fixes manual release validation to read metadata from the selected tag commit and sets explicit `GH_REPO` for checkout-less publish jobs. Its latest check did not run any project step because GitHub refused to allocate a runner under the current spending limit.
- branch `chat/pin-first-party-actions` pins first-party GitHub Actions to exact commit SHAs; it is intentionally not merged without restored CI.

## Manual/decision gates remaining

1. Restore GitHub Actions runner access. The pre-authorized path is to make the repository public; current Chat tooling cannot change repository visibility, so this requires a manual GitHub UI/admin action.
2. Run the deferred real Stage 4 ChatGPT -> Yandex -> Windows -> ChatGPT acceptance.
3. Choose a project license or explicitly decide to keep the project proprietary/private. If the repository is made public only for Actions, `LicenseRef-UNLICENSED` still means no open-source license has been granted.
4. Enable GitHub branch protection/ruleset for `main` when available through manual settings/tooling.
5. After CI resumes and PR #25 is validated/merged, deliberately create the first `v0.2.0` tag and verify generated GitHub Release assets/checksums.
6. Add a real licensed/owned musical corpus before making subjective professional-quality claims for reference mastering.

See `STAGE20_OPERATIONS.md` for the operational checklist and `KNOWN_ISSUES.md` for the remaining gaps.
