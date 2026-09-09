# Agent Session Temporary-Chat authenticated loopback re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-05**

Triggering PR: **#149**

Triggering reviewed HEAD: `8ecb7181ed24ed247afbdafb39568cfee0c7b4a6`

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable repository skills at the triggering HEAD:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/source-code-research/SKILL.md` v1.0
- `.agents/skills/code-review/SKILL.md` v1.1

This re-entry is required because fresh semantic review found a new release-critical local-IPC/controller-authentication failure class. Production implementation is blocked until this brief selects a bounded mechanism. The generic Delegation model, one-shot Temporary profile, public six-tool surface and parked Prime work remain outside the change.

## 1. Triggering finding and development-side falsification

Fresh ordinary-ChatGPT review of exact HEAD `8ecb7181ed24ed247afbdafb39568cfee0c7b4a6` reported a P1: the launcher and MV3 extension trust whichever process owns fixed loopback endpoint `127.0.0.1:3078`.

The finding survives development-side falsification.

Current controller ordering is:

```text
parse inputs
 -> construct TemporaryControllerRuntime
 -> write preflight.json for prepared/open delegation
 -> construct/bind ThreadingHTTPServer(127.0.0.1:3078)
```

Therefore a process that already owns port 3078 can coexist long enough for the exact child to write genuine `preflight.json`, after which the child can fail its bind. Current launcher `/health` acceptance checks response shape and child liveness only around the request; it does not authenticate the listener as the spawned exact-archive process.

Current extension traffic also uses raw bearer capabilities on the unauthenticated fixed origin:

- preflight sends raw `preflight_id`;
- later `/status`, authority, delivery and capture traffic sends raw private `run_id`;
- responses are unsigned.

A wrong loopback listener can therefore learn those bearer values and forge a self-consistent handoff/authority conversation. Exact extension bytes, one-Send claims, prompt checks and source locks do not defeat that endpoint-confusion path.

This attacker model does **not** require a fully privileged local administrator, modification of Git objects, or mutation of the running launcher. It requires only an ordinary same-machine process able to bind an unused user TCP port before CAP.

## 2. Exact stage question

> What is the smallest mechanism that makes every consequence-relevant extension/controller exchange authenticate the intended CAP controller rather than merely the fixed loopback address, while preserving controller restart reconciliation and the one-shot ephemeral Temporary profile?

Required invariants:

- the process owning `127.0.0.1:3078` cannot obtain or forge Temporary Send authority merely by speaking the public JSON protocol;
- raw `preflight_id` and raw private durable `run_id` are not transmitted to an untrusted loopback listener;
- the extension must authenticate controller responses **before** consuming handoff, status, authority, delivery or capture data;
- requests must likewise be authenticated before controller state transition handlers execute;
- wrong/pre-bound/takeover listeners fail closed with zero task navigation and zero physical Send;
- surviving original MV3 owner + restarted genuine controller can still reconcile from the same durable `run_id` without blind relaunch/resend;
- existing exact-source/runtime attestation remains required and independent of transport authentication;
- complete MV3/browser lifetime loss still does not recreate authority.

Out of scope:

- persistent conversation identity;
- Native Messaging packaging or installation;
- general local RPC framework;
- TLS/PKI service infrastructure;
- persistent browser lease or new durable replay database;
- Prime / Existing-Session Delivery / scheduler work;
- defending against a fully privileged attacker that can read CAP private state or inject code into the trusted processes.

## 3. Architecture lineage against `ARCHITECTURE_REUSE_BASELINE.md`

### Bounded Agent Session / Delegation lifecycle — `KEEP`

Provider-neutral deterministic delegation identity, durable private `run_id`, one delivery identity and result correlation stay unchanged.

### First-provider browser delivery ownership — `REFINE`

Keep the current MV3 live owner, opaque task launch handle and IndexedDB one-delivery claim. Refine only the browser-to-controller transport so that loopback address ownership is not treated as controller identity.

### Capability authorization / consequence policy — `KEEP`

Project Control Plane/controller remains the sole source of Send authority. The transport change exists to preserve this already selected boundary; it does not delegate authority to the browser or a new service.

### Multi-chat/provider browser adaptation — `KEEP`

Keep the narrow project `chatgpt-temporary` adapter. No generic provider framework is introduced.

### Native Messaging / browser-managed native host — `DEFER`

Chrome Native Messaging would give the browser a stronger host identity/channel, but it adds `nativeMessaging` permission, host registration/install/packaging requirements and a different lifecycle boundary. The current manifest intentionally has only the pinned loopback host permission. This is disproportionate for closing one #149 local IPC defect and is deferred to a later stage if packaging/provider needs justify it.

## 4. Engineering-domain evidence

This failure belongs primarily to **local IPC endpoint authentication**, not agent orchestration.

### Windows TCP ownership is observable but not sufficient as the sole trust primitive

Microsoft documents that `Get-NetTCPConnection` exposes `OwningProcess`, and the Win32 `MIB_TCPTABLE_OWNER_PID` / `GetExtendedTcpTable` APIs map TCP endpoints to PIDs.

Sources:

- https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-nettcpconnection
- https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcptable_owner_pid

This is useful defense-in-depth for the physical launcher, but a point-in-time PID/socket observation alone does not authenticate a later extension exchange after controller death/port takeover.

### HMAC authenticates messages with a shared secret

NIST FIPS 198-1 defines HMAC as a keyed-hash message authentication mechanism using a shared secret key.

Source: https://csrc.nist.gov/pubs/fips/198-1/final

Python stdlib provides HMAC and constant-time digest comparison. Chrome MV3 service workers have Web Crypto `SubtleCrypto`; MDN documents HMAC support for `verify()` and that Web Crypto is available in Web Workers.

Sources:

- https://docs.python.org/3/library/hmac.html
- https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/verify
- https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto

No external library or additional service is required.

### Source-code-research disposition

No public agent runtime is adopted or replaced for this mechanism. The strongest evidence is OS/socket ownership plus standard message-authentication primitives; per `source-code-research`, forcing another agent-repository comparison would be weaker than the direct engineering-domain evidence. Existing project source itself is the implementation under test.

## 5. Materially distinct approaches

### A — Require port 3078 to be free, then verify listener PID once

Mechanism:

```text
port free
 -> start controller
 -> Get-NetTCPConnection proves OwningProcess == spawned PID
 -> open preflight
```

Strength: closes the exact pre-bound-listener interleaving and provides useful operational evidence.

Failure: controller may later die and another ordinary process may acquire 3078 before subsequent extension `/status` or `/authorize-send` traffic. The extension still has no cryptographic proof of response origin. Repeating PID checks from PowerShell cannot cover every asynchronous browser request.

Decision: **REJECT as sole authority; KEEP as defense-in-depth / acceptance evidence**.

### B — Keep raw bearer tokens but add a health challenge

A launcher-generated challenge can authenticate one `/health` response only if the responder already holds a secret not exposed to the wrong listener. If the same bearer secret is sent to the listener during the challenge, the listener learns it and can forge subsequent responses. A one-time health proof also does not bind later browser traffic.

Decision: **REJECT**.

### C — TLS on localhost with an ephemeral/self-signed certificate

Strength: channel authentication can solve listener confusion.

Cost: certificate generation, trust/pinning, browser-extension fetch behavior and lifecycle/rotation add unnecessary PKI complexity for one local fixed adapter.

Decision: **NOT SELECTED**.

### D — Chrome Native Messaging

Strength: browser-managed named native host and no public TCP listener.

Cost/boundary impact: new extension permission, manifest/registry host registration, install/update/packaging lifecycle and a materially larger product boundary. It would also contradict the current #149 claim that the extension has no `nativeMessaging` authority.

Decision: **DEFER**.

### E — Authenticated request/response MAC over existing loopback HTTP — SELECTED

Use the existing high-entropy capabilities as HMAC keys but **never transmit those keys raw**.

Two phases:

```text
preflight phase key = preflight_id
post-commit phase key = durable private run_id
```

For each request the MV3 worker creates a fresh random 32-byte nonce and exact UTF-8 JSON body bytes. Authentication input is domain separated and includes at least:

```text
CAP_AGENT_LOOPBACK_AUTH_V1
request
HTTP method
exact path
request nonce
SHA-256(exact request body bytes)
```

The extension sends nonce + HMAC headers only. It does not send raw `preflight_id` or raw `run_id` in headers or wire JSON.

Controller verifies MAC before dispatching a state transition. After transport verification it may inject the already-known internal capability into the in-process mapping so existing state-machine correlation contracts can remain unchanged.

Every response is likewise authenticated before the extension parses/acts on JSON:

```text
CAP_AGENT_LOOPBACK_AUTH_V1
response
HTTP method
exact path
request nonce
HTTP status
SHA-256(exact response body bytes)
```

The extension reads response bytes/text, verifies HMAC under the same phase key, and only then parses the response and mutates `LIVE_LAUNCHES` or acts on authority/result data.

A wrong listener sees only nonce, body and MAC. It cannot recover the HMAC key or forge a different valid body. A listener that takes the port after controller restart still cannot forge run-key responses.

Decision: **SELECTED / NARROW**.

## 6. Minimal protocol and implementation boundary

### Wire request headers

Use fixed versioned names, for example:

```text
X-CAP-Agent-Auth-Version: 1
X-CAP-Agent-Auth-Nonce: <64 lowercase hex>
X-CAP-Agent-Auth-Mac: <64 lowercase hex HMAC-SHA256>
Content-Type: application/json
```

Do not send:

```text
X-CAP-Agent-Preflight: <preflight_id>
X-CAP-Agent-Token: <run_id>
```

and do not serialize `preflight_id` / `run_id` as wire JSON fields merely for transport authentication.

### Wire response headers

Return:

```text
X-CAP-Agent-Auth-Version: 1
X-CAP-Agent-Auth-Nonce: <same request nonce>
X-CAP-Agent-Auth-Mac: <response HMAC>
```

The extension must reject missing/wrong version, nonce or MAC before parsing/using response JSON.

### Replay posture

Per-request random nonce prevents passive transcript substitution in the live process. The controller should maintain a small bounded in-memory seen-nonce set per phase/key and reject duplicate nonces during that process lifetime.

Do **not** introduce a new durable replay database. Existing durable delegation/delivery state remains the authority that makes repeated committed effects idempotent/fail-closed across controller restarts. A replay after restart cannot forge a new MAC for a different nonce/body and exact one-shot state still prevents duplicate Send authority.

### Controller bind ordering

Defense in depth: bind the `ThreadingHTTPServer` socket **before** publishing `preflight.json` / creating browser-visible preflight capability. Use a server construction path that can bind first, then construct/attach runtime and activate serving.

If bind fails, zero preflight projection/browser launch authority must exist.

### Launcher listener proof

Before opening the neutral preflight URL, production Windows launcher should additionally prove that the listening `127.0.0.1:3078` socket is owned by the spawned controller PID. This is operational/source-qualification evidence, not the sole cryptographic authority boundary.

## 7. Failure/crash matrix

| Boundary / fault | Required outcome |
|---|---|
| rogue process owns 3078 before launch | exact child cannot publish usable preflight; launcher fails closed; zero browser task navigation/Send |
| rogue `/health` response | cannot satisfy controller PID/bind proof and cannot authenticate consequence traffic |
| exact child dies after launcher listener proof, rogue takes 3078 | extension MAC verification fails; zero new Send/result authority |
| rogue receives preflight request | raw preflight key absent; cannot forge authenticated handoff response |
| rogue receives post-commit `/status` or `/authorize-send` | raw run key absent; cannot forge authenticated response |
| response body modified with old MAC | reject before JSON parse/use |
| wrong response nonce/version/MAC | reject before state/action |
| duplicate request nonce in same controller lifetime | reject before operation |
| preflight commit ACK lost after real commit | original same MV3 owner retries/reconciles using authenticated run-key `/status`; existing UNKNOWN semantics preserved |
| controller restarts after durable launch commit while original MV3 owner survives | restarted controller recovers same private run key; authenticated `/status` reconciliation remains possible |
| controller restarts before commit | prepared/open semantics and same-live-owner rebind remain as current contract; new genuine preflight uses fresh preflight key |
| MV3/browser lifetime lost | no live key/owner recovery; existing fail-closed profile unchanged |
| wrong installed extension/runtime generation | existing runtime/source attestation fails independently of MAC authentication |

Maximum additional physical Send caused by any authentication/provenance failure above: **zero**.

## 8. Acceptance shields

Focused deterministic/behavioral tests must prove at least:

1. production controller binds 3078 before `preflight.json`/preflight capability publication;
2. occupied 3078 causes controller/launcher fail-closed with no fresh preflight projection and no browser opening;
3. launcher proves the production listener is owned by the spawned controller PID before opening preflight;
4. real controller + exact extension preflight succeeds with authenticated request and authenticated response;
5. fake listener returning valid-looking `/health`, `/preflight`, `/status` and `/authorize-send` JSON without the HMAC key cannot cause a browser claim or physical Send;
6. raw `preflight_id` is absent from wire request headers/body;
7. raw `run_id` is absent from wire request headers/body after handoff;
8. altered body, altered path, wrong nonce, replayed same-process nonce, missing/wrong response MAC and wrong status binding all fail before state/action;
9. extension verifies response authentication before `JSON.parse`/handoff acceptance;
10. controller verifies request authentication before state transition dispatch;
11. preflight commit ACK-loss reconciliation remains functional over authenticated transport;
12. controller restart with same durable run key remains reconcilable by the surviving original MV3 owner;
13. existing exact composer, one-Send, B1/B2 browser-loss, capture/result and source-provenance tests remain green;
14. execution generation changes because `background.js` changes;
15. final physical A/B1/B2 are rerun only after a fresh semantic PASS on the eventual exact HEAD.

## 9. Scope discipline

This change must not:

- add `nativeMessaging`;
- add a new public Chat-facing tool;
- make the extension a Control Plane authority;
- create a generic IPC/auth framework for unrelated capabilities;
- add persistent session identity, scheduler, Prime, MimiSeek or reviewer semantics;
- move the durable private `run_id` into browser storage or provider-visible state;
- weaken exact source/runtime attestation because transport is now authenticated.

The selected mechanism is an adapter-private authenticated transport beneath the existing generic Delegation authority.

## 10. Decision

**NARROW**.

Implement only authenticated loopback request/response binding plus bind/PID defense-in-depth for the existing `chatgpt-temporary` adapter. Preserve all current generic Delegation and ephemeral one-shot semantics.

The fresh review on `8ecb7181ed24ed247afbdafb39568cfee0c7b4a6` is now stale once implementation begins. After implementation, focused adversarial tests and all preliminary hosted gates, freeze the new exact HEAD and require another genuinely fresh ordinary-ChatGPT semantic review before physical A/B1/B2 qualification.