# Roadmap v1.4

Это исполняемый план, а не список обещаний. Source of truth по факту — этот файл + `CURRENT_STATE.md`; operational evidence хранится отдельно. Connector architecture additionally follows `CONNECTOR_ARCHITECTURE.md` and ADR-009.

## Правила статусов

- **done** — собственный exit gate этапа доказан;
- **partial** — полезная реализация есть, но один или несколько exit gates не закрыты;
- **planned** — обязательная работа ещё не начата;
- **conditional** — выполняется только после конкретного доказанного сценария/пробела.

Этапы **не являются строго линейной цепочкой**. Независимая локальная capability может быть завершена, пока более ранний внешний/manual gate остаётся partial. Нельзя помечать этап `done` только потому, что разработка ушла дальше.

## Horizon A — Core

### Stage 0 — Reality baseline + Project Binding — partial

Done:
- explicit Project Binding;
- Chat -> GitHub branch/edit/PR/CI/merge path;
- versioned requirements отдельно от runtime profile.

Open exit gate:
- окончательный Hosted Chat -> local Windows execution path через Stage 4 connector.

### Stage 1 — Rust vertical architecture — done

Rust выполняет binding -> policy -> artifact -> typed tool -> validation -> contract result. Python остаётся только behavioral oracle.

### Stage 2 — Contracts — done

Embedded schemas существуют для tool request/result, artifact, policy decision, confirmation, secret reference, jobs и relay request/response.

### Stage 3 — Project Memory + Bootstrap + Skills — done

Новая сессия получает минимальный project context и релевантный capability slice вместо полного дампа истории.

## Horizon B — Safe execution

### Stage 4 — Hosted Chat -> local connector — partial / provider-neutral core accepted

Architecture rule:
- **there is no canonical cloud provider**;
- canonical boundaries are standard MCP/relay contracts plus the local Project Binding/policy/execution boundary;
- Yandex, VPS, container hosting, reverse tunnels and future providers are replaceable deployment choices;
- local capability code must not branch on provider identity.

Implemented and proved at local/contract level:
- provider-neutral Windows polling configuration stores only `endpoint + secret_ref`;
- any normal HTTPS endpoint satisfying the polling contract can be configured;
- outbound-only Windows `poll/result/offline` protocol;
- independent agent/remote tokens for polling relay deployments;
- Credential Manager local secret;
- immutable task/result semantics and lost-ACK response cache;
- explicit start/status/stop, no autostart;
- exact remote allowlist `local_ping`, `runtime_self_test`;
- Rust `relay-server` is a provider-neutral polling-relay reference implementation with SQLite short-lived state and bounded retention;
- existing Yandex Function/Object Storage path is a provider-specific implementation of the same local polling contract;
- real Yandex backend -> Windows acceptance passed 2026-08-09:
  - `local_ping`: local execution proved;
  - `runtime_self_test`: success;
  - controlled write/read + cleanup: passed;
  - relay returned to disabled state;
- Rust relay-server round-trip, auth and failure paths are covered by dedicated CI/integration tests.

Preferred MCP direction:

```text
MCP-capable caller
  -> standard MCP Streamable HTTP
  -> replaceable HTTPS ingress
     (direct host / reverse proxy / mature reverse tunnel)
  -> loopback local MCP boundary
  -> agent-platform policy + typed local execution
```

The standard MCP boundary should use the official Rust MCP SDK (`rmcp`). Do not continue growing a hand-written standards implementation. NAT traversal/publication should reuse mature solutions such as frp or zrok rather than becoming a platform subsystem.

Polling relay remains a compatibility profile:

```text
remote caller / compatibility ingress
  -> any compatible HTTPS polling backend
  -> outbound Windows poll
  -> agent-platform local execution
  -> result back through the same backend
```

Use the polling profile for serverless or other environments where a transparent reverse tunnel is unavailable, undesirable or unsupported.

GPT Action remains a compatibility ingress where it is the available Hosted Chat integration. The existing Yandex API Gateway requirement is specific to that Yandex deployment's Authorization-header behavior, not a platform invariant.

Remaining Stage 4 exit gates:

1. Real request originated by Hosted Chat through a supported ingress -> user Windows `agent-platform.exe` -> local execution -> result back to Hosted Chat.
2. One real **non-Yandex** remote -> Windows acceptance, using either:
   - standard tunneled MCP; or
   - the Rust `relay-server` polling backend.

Until the Hosted Chat gate passes, do not expose mastering/REAPER/media/distribution capabilities remotely.

Provider portability is not considered fully proved by CI alone. The Yandex acceptance remains valid evidence for one backend, while the second live path proves that deployment choice is actually replaceable.

### Stage 5 — MCP aggregation — conditional

Do not add ToolHive/1MCP/n8n-style aggregation unless direct/native surface produces a measured governance/context/isolation problem.

Using the official MCP SDK for the platform's own standard MCP endpoint is **not** MCP aggregation. Third-party stdio/SSE/HTTP bridges may use mature MCP proxy tools only when a concrete compatibility requirement appears.

### Stage 6 — Tool Manifest + selection + hardened PEP — done

Executable fail-closed contract enforces locked executor, enabled state, quality, reliability, determinism, execution path, fallback agreement and cost. Unknown fields fail closed. Runtime profile is derived from the same locked selections.

### Stage 7 — Secret Store — done

Windows Credential Manager, executor ACL, short-lived zeroized secret buffer; no custom cryptography/vault daemon.

### Stage 8 — Artifact hardening/staging — done

SHA-256 identity, pending lifecycle, atomic publish, per-artifact locks, conservative recovery and allowlisted temporary external staging. Workflow processing uses immutable captured snapshots.

### Stage 9 — Supervisor/service — conditional

Add only if explicit connector lifecycle becomes operationally insufficient. No permanent service just for convenience. A third-party tunnel process is an edge deployment component and must not become a second orchestration core.

### Stage 10 — CI + supply chain — done baseline

Current baseline:
- `ci / verify-windows` runs on every pull request and every `main` push;
- Windows fmt/Clippy/tests/contracts/Python parity/release build;
- pinned Rust 1.97.1 and hosted FFmpeg 9.0.0;
- all first-party GitHub Actions pinned by immutable commit SHA;
- every checkout uses `persist-credentials: false`;
- scoped Stage 4 and real Stage 19 E2E;
- checksum-pinned cargo-deny enforcing dependency licenses/bans/sources and RustSec advisories;
- explicit evidence-driven dependency-license allow-list with no package exceptions;
- checksum-pinned Gitleaks full-history scan with full redaction;
- pinned reproducible CycloneDX SBOM;
- checksum-pinned cargo-about Windows third-party license notices;
- weekly grouped Dependabot;
- active `main-protection` repository ruleset requiring PR flow, strict up-to-date `verify-windows` + `gitleaks-history`, linear history, and blocking deletion/force-push with no bypass actors.

## Horizon C — Professional media/audio

### Stage 11 — FFmpeg adapter — done

Typed inspect/validate/convert/extract/normalize/mux. No arbitrary shell/FFmpeg arguments. EBU R128 QC, sample-rate preservation and duration-aware execution timeouts are regression-tested.

### Stage 12 — REAPER adapter — done

Typed Rust -> limited Lua/ReaScript path. Real user Windows acceptance passed 2026-08-08.

### Stage 13 — Mastering analysis/decision — done

Profile-aware technical LUFS/true-peak/LRA decision layer and safe-auto review gate.

### Stage 14 — Persistent job runtime — done

File-backed atomic JobStore with idempotency, checkpoint, retry/cancel and cross-process persistence. Per-job OS execution lock guarantees one physical executor for one job.

### Stage 15 — Technical delivery mastering — done

Immutable source snapshot -> Stage 13 decision -> typed Stage 11 processing -> final QC -> Artifact Store. Exact repeat returns the same persisted result.

### Stage 19 — Reference mastering — done

Pinned Matchering 2.0.6 edge process with target/reference SHA identity, PCM24 intermediate checks, Rust final delivery QC, sample-rate integrity and idempotent persisted job.

Technical synthetic benchmark is green; a real musical listening corpus remains a quality-validation gap, not an integration gap.

## Horizon D — Expand only from concrete demand

### Stage 16 — Browser automation — conditional

When a real scenario appears: API/connector first, then Playwright/Browser MCP, UI automation last. Node may be edge runtime, not core dependency.

### Stage 17 — Video production — conditional

Use typed FFmpeg composition, Blender API/addons and external generators through existing artifact/policy/job boundaries. Do not build a second orchestration core.

### Stage 18 — Distribution — conditional

Security prerequisite is available:

```text
fresh policy preview
  -> idempotent short-lived confirmation prepare
  -> explicit user confirmation
  -> fresh policy re-evaluation
  -> atomic one-shot ConfirmationPermit
  -> external executor consumes permit by value
```

No distribution executor is implemented yet. Do not expose side effects until one concrete platform scenario and its policy/acceptance tests exist.

## Horizon E — Operations

### Stage 20 — Operations audit — partial / manual-gated

Automated/hardened baseline completed:
- job execution ownership and immutable workflow inputs;
- executable capability contracts and runtime-profile drift detection;
- one-shot guarded confirmations;
- provider-neutral local polling transport (`endpoint + secret_ref`);
- provider-neutral Rust polling relay reference implementation;
- real Yandex->Windows polling-backend acceptance retained as one backend's evidence;
- explicit connector architecture preventing Yandex/VPS/cloud-provider identity from becoming a core contract;
- duration-aware FFmpeg execution/logging;
- public repository under standard MIT License;
- always-on Windows CI with immutable-SHA Actions and no persisted checkout credentials;
- active `main-protection` ruleset with no bypass actors;
- direct checksum-pinned dependency/advisory/license policy;
- green full-history secret scan;
- reproducible SBOM;
- Windows third-party license notices with policy parity;
- exact-tag version validation;
- immutable tag-gated GitHub Release workflow;
- non-publishing Release Package E2E proving real Windows binary + SBOM + project/dependency licenses -> exact ZIP -> SHA256SUMS;
- GitHub provenance attestation before release publication;
- raw `.exe` excluded from standalone public Release assets.

Remaining mandatory manual gates:
1. complete real Hosted Chat-originated Stage 4 round trip through a supported ingress;
2. prove one real non-Yandex connector path so provider portability is runtime evidence, not only architecture/code evidence;
3. create the first explicit `v0.2.0` tag and inspect the real GitHub Release assets/checksums/provenance.

Next connector engineering change set:
- implement standard local MCP Streamable HTTP using official `rmcp`;
- keep the current GPT Action and polling relay as compatibility surfaces;
- use mature reverse tunnel/proxy software for live non-Yandex acceptance instead of adding custom tunnel code.

Conditional follow-up (not Stage 20 blockers):
- compare frp/zrok/other mature tunnel profiles only when deployment requirements warrant it;
- real music corpus/human listening before subjective professional-quality claims;
- support/donation addresses when available;
- unresolved-artifact operator cleanup if operational demand appears;
- Job/ConfirmationStore indexing only after measured growth;
- supervisor/service only if explicit lifecycle becomes insufficient;
- Python oracle removal after a separate parity/stability gate.

Detailed checklist: `project-context/STAGE20_OPERATIONS.md`.

## Definition of Done for future capabilities

1. Real scenario and explicit Project Binding.
2. Typed capability; no arbitrary command surface.
3. Versioned/fail-closed config and policy enforcement in code.
4. Artifact identity refers to the exact bytes processed.
5. Idempotency/retry/execution ownership defined where work is stateful.
6. External side effect requires a consumed confirmation permit.
7. Positive, negative and integration tests proportional к риску.
8. New dependency/process/service has a measured reason and replacement/removal plan.
9. Runtime profile/evidence does not replace versioned requirements.
10. Documentation is updated in the same development cycle.
11. Network/cloud provider identity must not enter the local capability contract without a separately proven provider-specific requirement.
