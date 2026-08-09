# Current State

## Snapshot

Architecture v1.4 is **Rust-first / native-edge**. Chat is primary intelligence; one local `agent-platform.exe` owns contracts, Project Binding, locked capability selection, policy, guarded confirmations, artifacts, persistent jobs and secret ACL. Mature tools remain typed edge executors.

Python v0.1 is retained only as a behavioral oracle for parity. It is not the target runtime.

Repository is **public** and licensed under the standard **MIT License** with no additional mandatory conditions. Project support/donations are voluntary and separate from MIT rights.

## Stage status

| Stage | Status | Current evidence |
| --- | --- | --- |
| 0 Reality baseline + Binding | partial | Binding/GitHub proven; real Hosted Chat -> Windows round trip still pending |
| 1 Rust vertical core | done | binding -> policy -> artifact -> typed tool -> validated result |
| 2 Contracts | done | embedded schemas for tool/artifact/policy/confirmation/secret/job/relay |
| 3 Memory/bootstrap/skills | done | minimal project context + bootstrap path |
| 4 Hosted transport | partial / E2E-ready | Yandex relay hosted E2E green; final real ChatGPT-originated call pending |
| 5 MCP aggregation | conditional | no extra aggregator justified |
| 6 Capability selection + PEP | done | fail-closed quality/reliability/determinism/path/fallback/cost gates |
| 7 Secret Store | done | Windows Credential Manager + executor ACL |
| 8 Artifact hardening/staging | done | immutable SHA-verified inputs, recovery, controlled staging |
| 9 Supervisor/service | conditional | current explicit relay lifecycle is sufficient |
| 10 CI + supply chain | done baseline | always-on Windows CI, SHA-pinned Actions, secret/license/advisory/SBOM gates |
| 11 FFmpeg adapter | done | typed operations, EBU QC, duration-aware timeouts |
| 12 REAPER adapter | done | real user Windows acceptance passed 2026-08-08 |
| 13 Mastering analysis | done | profile-aware technical decision/safe-auto gate |
| 14 Persistent jobs | done | idempotency/checkpoints/retry + exclusive physical execution |
| 15 Technical mastering | done | immutable input snapshot + final QC + idempotent master |
| 16 Browser automation | conditional | no concrete scenario selected |
| 17 Video production | conditional | no concrete scenario selected |
| 18 Distribution | conditional | confirmation primitive done; external executors intentionally absent |
| 19 Reference mastering | done | real pinned Matchering engine + technical benchmark |
| 20 Operations audit | partial / manual-gated | automated hardening complete; branch ruleset, real Stage 4 call and first release remain |

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

## Stage 4 transport

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

Hosted CI proves: explicit configure/start/status/stop, independent local/remote tokens, Credential Manager storage, exact remote allowlist (`local_ping`, `runtime_self_test`), immutable task/result rendezvous, lost-ACK retry without local re-execution, minimal unauthenticated health and offline lifecycle.

The final ChatGPT-originated round trip is still manual. Until it passes, higher-value local capabilities remain unavailable through the remote surface.

## Public CI / supply chain

Current enforced baseline:

- `ci / verify-windows` runs on every PR and every `main` push;
- every `actions/checkout` reference is immutable-SHA pinned and uses `persist-credentials: false`;
- all first-party GitHub Actions are immutable-SHA pinned by repository-wide regression test;
- Rust 1.97.1 and hosted FFmpeg 9.0.0 are pinned;
- checksum-pinned cargo-deny 0.20.2 enforces dependency licenses, bans, sources and RustSec advisories;
- dependency license allow-list is explicit and evidence-driven with no package-level license exceptions;
- checksum-pinned Gitleaks 8.30.1 scans complete reachable git history with full redaction; the first public-history scan was green;
- reproducible CycloneDX SBOM is generated with pinned cargo-cyclonedx 0.5.9;
- checksum-pinned cargo-about 0.9.1 generates Windows third-party notices; notice policy must equal cargo-deny license policy;
- weekly grouped Dependabot updates remain enabled.

## Release path

The tag-gated release path now requires an existing exact `vX.Y.Z` reachable from `main` and validates Rust/Python/oracle version alignment from that exact tag.

A real non-publishing Release Package E2E already proves cross-job assembly of:

```text
Windows release binary
+ CycloneDX SBOM
+ MIT LICENSE
+ THIRD_PARTY_LICENSES.html
  -> exact-content ZIP
  -> SHA256SUMS self-check
```

The raw `.exe` is not a standalone GitHub Release asset. The public distribution ZIP always carries the project and dependency license material. `SHA256SUMS` covers the binary, SBOM, license files and ZIP. The release workflow performs GitHub build-provenance attestation before `gh release create`; attestation failure blocks publication. Existing releases are never overwritten.

The first actual `v0.2.0` tag/release has intentionally not been created yet, so real tag-triggered publication/attestation remains a manual acceptance gate even though the package pipeline itself is E2E-tested.

## Manual gates remaining

1. Enable a GitHub branch ruleset for `main`, requiring the stable `verify-windows` and `gitleaks-history` checks and PR-based merging.
2. Run the real Stage 4 ChatGPT -> Yandex -> Windows -> ChatGPT acceptance.
3. Deliberately push the first `v0.2.0` tag and verify generated Release assets, checksums and provenance.

## Conditional/non-blocking follow-up

- real licensed/owned music corpus + human listening acceptance before subjective professional-quality claims;
- support/donation addresses when available;
- ArtifactStore unresolved-orphan operator cleanup when operational demand appears;
- Job/ConfirmationStore indexing/retention only after measured growth;
- Python oracle removal after a separate parity/stability gate;
- Stages 16–18 only from concrete product scenarios.

See `STAGE20_OPERATIONS.md`, `ROADMAP.md` and `KNOWN_ISSUES.md`.
