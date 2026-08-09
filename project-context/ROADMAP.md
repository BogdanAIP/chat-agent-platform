# Roadmap v1.4

Это исполняемый план, а не список обещаний. Source of truth по факту — этот файл + `CURRENT_STATE.md`; operational evidence хранится отдельно. Connector architecture additionally follows `CONNECTOR_ARCHITECTURE.md` and ADR-009.

## Правила статусов

- **done** — собственный exit gate этапа доказан;
- **partial** — полезная реализация есть, но один или несколько exit gates не закрыты;
- **planned** — обязательная работа ещё не начата;
- **conditional** — выполняется только после конкретного доказанного сценария/пробела.

Этапы **не являются строго линейной цепочкой**. Независимая локальная capability может быть завершена, пока более ранний внешний/manual gate остаётся partial. Нельзя помечать этап `done` только потому, что разработка ушла дальше.

## Horizon A — Core

### Stage 0 — Reality baseline + Project Binding — done

Proved:
- explicit Project Binding;
- Chat -> GitHub branch/edit/PR/CI/merge path;
- versioned requirements отдельно от runtime profile;
- real Hosted Chat -> installed plugin/app -> Yandex -> local Windows agent -> response back to ChatGPT on 2026-08-06.

### Stage 1 — Rust vertical architecture — done

Rust выполняет binding -> policy -> artifact -> typed tool -> validation -> contract result. Python остаётся только behavioral oracle.

### Stage 2 — Contracts — done

Embedded schemas существуют для tool request/result, artifact, policy decision, confirmation, secret reference, jobs и relay request/response.

### Stage 3 — Project Memory + Bootstrap + Skills — done

Новая сессия получает минимальный project context и релевантный capability slice вместо полного дампа истории.

## Horizon B — Safe execution

### Stage 4 — Hosted Chat -> local connector — done

Original Stage 4 exit gate is complete.

Real evidence:
- on 2026-08-06 the installed ChatGPT integration `Music Video MCP Yandex Test` successfully executed `local_ping` through the Yandex-hosted gateway and returned a response from local Windows machine `ID182019`, Windows 11, agent `0.2.1`, back to ChatGPT;
- on 2026-08-09 the current Yandex polling backend separately passed local `local_ping`, `runtime_self_test`, controlled write/read, cleanup and clean relay shutdown;
- offline behavior was observed: a later ChatGPT-originated `runtime_self_test` reported `agent_offline` when the local agent was stopped.

Therefore **Hosted Chat -> remote integration -> local Windows execution -> response** is no longer an open Stage 4 gate.

Architecture rule:
- there is **no canonical cloud provider**;
- NAT traversal, TLS/public routing and tunnel multiplexing are mature edge infrastructure, not platform subsystems;
- local capability code must not branch on provider/tunnel identity;
- `agent-platform.exe` remains the authority for Project Binding, authentication, policy and typed local execution.

#### Direct loopback ingress — implemented and process-tested

The preferred compatibility path now exists in the same Rust binary:

```text
mature HTTPS tunnel
  -> 127.0.0.1:8787/gpt
  -> X-MCP-Token auth
  -> Project Binding + policy
  -> shared local allowlisted dispatch
```

Implemented:
- required capability `transport.local_ingress` / executor `rust.local.ingress`;
- loopback-only bind; no `0.0.0.0` mode;
- explicit foreground CLI (`ingress configure-token`, `ingress serve`, `ingress remove-token`);
- Windows Credential Manager-backed caller secret;
- exact allowlist `local_ping`, `runtime_self_test`;
- auth before dispatch;
- 8 KiB request limit and bounded concurrency;
- direct ingress and polling relay reuse one local operation dispatcher;
- compatibility `/gpt` + `X-MCP-Token` contract retained.

Windows Stage 4 E2E proves a real process, not only a handler unit test:
- stores a unique token in Credential Manager;
- starts the real `agent-platform.exe` on an ephemeral loopback port;
- proves `401` without the token;
- proves authenticated `local_ping` returns `200` and `executed_locally=true`;
- stops the process and removes the credential.

The existing polling relay remains green as rollback/fallback:
- provider-neutral Windows `endpoint + secret_ref` configuration;
- outbound `poll/result/offline` lifecycle;
- Rust `relay-server` reference backend with bounded SQLite retention;
- Yandex backend retained as historical/tested adapter.

#### Connector modernization after Stage 4

Next live acceptance deliberately changes only network reachability:

```text
existing ChatGPT action/plugin
  -> mature non-Yandex public HTTPS tunnel
  -> 127.0.0.1:8787/gpt
  -> agent-platform
```

If this passes, Yandex/VPS/custom polling state is proven unnecessary for the normal current ChatGPT action path.

After that, add the target standard protocol:

```text
MCP-capable caller
  -> public HTTPS /mcp
  -> official rmcp adapter
  -> same agent-platform policy + typed execution
```

Rules:
- use official Rust MCP SDK `rmcp`; do not grow the hand-written MCP standards implementation;
- public HTTPS/reverse tunnel is sufficient when acceptable;
- OpenAI Secure MCP Tunnel is optional private reachability, not a prerequisite;
- mature tunnel/proxy products remain replaceable deployment choices;
- keep polling/Yandex compatibility until direct non-Yandex and native MCP acceptance are both proven.

Remaining migration/deprecation evidence:
1. real non-Yandex ChatGPT -> mature HTTPS tunnel -> direct ingress -> Windows -> ChatGPT round trip;
2. native standard MCP `/mcp` call on the user's actual ChatGPT surface after `rmcp` exists.

These do not reopen Stage 4.

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

Add only if explicit ingress/connector lifecycle becomes operationally insufficient. No permanent service just for convenience. A third-party tunnel process is an edge deployment component and must not become a second orchestration core.

### Stage 10 — CI + supply chain — done baseline

Current baseline:
- `ci / verify-windows` runs on every pull request and every `main` push;
- Windows fmt/Clippy/tests/contracts/Python parity/release build;
- pinned Rust 1.97.1 and hosted FFmpeg 9.0.0;
- all first-party GitHub Actions pinned by immutable commit SHA;
- every checkout uses `persist-credentials: false`;
- Stage 4 Windows E2E covers direct loopback ingress plus legacy polling fallback;
- real Stage 19 E2E;
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

### Stage 20 — Operations audit — partial / release-gated

Automated/hardened baseline completed:
- job execution ownership and immutable workflow inputs;
- executable capability contracts and runtime-profile drift detection;
- one-shot guarded confirmations;
- direct loopback-only authenticated ingress in the main `agent-platform.exe`;
- Windows process-level ingress E2E with real Credential Manager/auth/local execution;
- polling transport/relay retained as provider-neutral fallback;
- real ChatGPT -> plugin -> Yandex -> Windows -> ChatGPT acceptance recorded;
- explicit connector architecture preventing provider/tunnel identity from becoming a core contract;
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

Remaining mandatory manual release gate:
1. create the first explicit `v0.2.0` tag and inspect the real GitHub Release assets/checksums/provenance.

Connector migration before deprecating Yandex compatibility:
- prove the direct `/gpt` path through one mature non-Yandex HTTPS tunnel from real ChatGPT;
- implement standard local MCP Streamable HTTP using official `rmcp`;
- test public HTTPS `/mcp` from the user's actual ChatGPT surface;
- only then decide whether the legacy polling/GPT Action/Yandex deployment can be retired.

Conditional follow-up:
- Secure MCP Tunnel as an optional OpenAI-private profile when useful and actually available;
- tunnel-specific recipes only for real deployment requirements;
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
11. Network/cloud/tunnel provider identity must not enter the local capability contract without a separately proven provider-specific requirement.
