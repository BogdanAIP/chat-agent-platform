# Composition-First Architecture

Status: **POST-#149 ARCHITECTURE LOCK — RESEARCH DIRECTION ONLY — NO PRODUCTION AUTHORITY**

This document records the intended architecture direction after PR #149 so the project does not drift back into building a large project-owned Agent Runtime or broad execution stacks by default.

It does **not** modify PR #149, does not change accepted `main`, does not authorize a new dependency, and does not bypass the repository's `stage-research`, `source-code-research`, code-review, CI, security or physical-acceptance gates.

The purpose is sequencing and scope control:

> **Build only the CAP trust/effect semantics that are genuinely project-specific. Reuse mature execution/session substrates through narrow adapters. Write custom runtime/executor machinery only when a measured conformance gap proves it is necessary.**

---

## 1. Target product shape

The preferred post-#149 architecture is:

```text
                         ordinary ChatGPT
                               |
                               v
                         CAP TRUST CORE
              identity / authorization / scope
              logical operation / ExpectedEffect
              ambiguity / reconciliation / provenance
              Verification Kernel / Finish Gate
                               |
       +-----------------------+------------------------+
       |                       |                        |
       v                       v                        v
    Sessions                 Desktop                   IoT
       |                       |                        |
 CCCC / #149               WinApp CLI            Home Assistant
 Prime optional            UFO/UFO²              Matter/MQTT via HA
                           OpenAdapt
                           Vision fallback

Browser remains a separate accepted capability path using the current
Playwright/project Browser boundary unless fresh evidence justifies change.
```

This is a **composition architecture**, not a plan to collapse all providers into one universal runtime.

Installed Windows applications should normally be treated as applications behind the generic Desktop capability, not as new CAP capability families requiring one adapter per product. Application-native APIs/COM/object models may be used internally by a qualified reusable Windows/application executor when they improve mechanics, but they are **not** the default CAP expansion strategy.

The same rule applies to web applications. A new web service should normally enter through the generic Browser capability and the accepted Playwright/project browser path. It should **not** imply a new CAP-native site/provider integration merely because the product is Figma, Google Sheets, Notion, Canva, a CRM/ERP or another browser application. Site-aware or site-specific mechanics are fallback implementation details justified only by a measured gap.

---

## 2. What CAP should remain responsible for

CAP is the trusted control/verification layer above interchangeable execution substrates.

CAP-owned semantics remain, unless separately researched and accepted otherwise:

```text
stable logical identity
capability / subject identity
consequence authorization and scope
operation / attempt identity
ExpectedEffect
freshness and provenance
untrusted-content fencing where required
PASS | FAIL | UNKNOWN
ambiguous-outcome reconciliation
no blind retry after unknown consequence
WorkingState for authoritative cross-capability operational facts
Verification Kernel
independent Finish Gate
exact source/runtime provenance where release-critical
provider conformance obligations
exactly-six public semantic tool surface unless separately accepted
```

An upstream transport/executor saying `accepted`, `success`, `invoked`, `sent` or `completed` is **evidence**, not CAP `PASS` and not whole-task `DONE`.

Canonical distinction:

```text
transport/executor accepted an action
              !=
required effect was freshly observed
              !=
whole task is complete
```

---

## 2.1 Consequence assurance floor and current implementation-depth map

Composition-first must not be interpreted as "any mature executor may sit below CAP if it can perform the action." Reuse is accepted only when the resulting path preserves the CAP consequence contract at the depth required by that effect class.

The project currently has strong common primitives, but **not every public or registered consequence-bearing path composes all of them at the same depth**. Treat that as an explicit integration state rather than implying that one physical "kernel process" already intercepts every effect.

### Assurance layers

Use the following layers when evaluating an existing CAP path or a new provider:

```text
A. authority / scope
   exact capability, subject, actor/environment and allowed consequence

B. pre-effect identity
   fresh current observation and target identity before mutation

C. declared effect
   bounded ExpectedEffect / postcondition known before delivery

D. bounded delivery
   one reviewed action; provider receipt is evidence only

E. fresh effect verification
   fresh same-subject/same-stream observation
   -> PASS | FAIL | UNKNOWN

F. ambiguity semantics
   delivery failure/ack loss/partial observation never becomes assumed success

G. durable operation / attempt settlement
   required where restart, retry, acknowledgement loss or duplicate delivery
   can repeat a consequence:
   operation identity + attempt identity + reconciliation + no blind retry

H. whole-task completion
   transition PASS != task DONE;
   use an independent Finish Gate when the path claims task completion

I. provenance / executed-byte closure
   required where source/runtime identity is release-critical

J. bypass resistance
   provider-native shell/write/admin/generic-tool authority must not create a
   parallel consequence path outside the admitted CAP boundary
```

Not every read-only observation needs all ten layers. Not every low-consequence one-shot action needs durable restart state. The rule is proportional:

```text
read-only observation
 -> A + bounded identity/provenance appropriate to the source

one bounded consequence with no accepted retry/restart semantics
 -> A+B+C+D+E+F

consequence that can be retried/resumed after ambiguous delivery
 -> A+B+C+D+E+F+G

procedure/task claiming completion
 -> required transition layers + H

release-critical external runtime/provider
 -> required effect layers + I + J
```

A provider may keep its native state model. CAP does not require every provider to inherit one universal class or state machine. It does require evidence that equivalent safety properties survive the adapter boundary.

### Current implementation-depth map

As of the post-#149 baseline researched for this PR, the accepted/public paths are intentionally heterogeneous:

| Path | Bounded authority | Fresh effect verification | Durable operation/attempt settlement | Independent completion boundary | Current interpretation |
|---|---|---|---|---|---|
| `workspace_read` | yes | read-only | n/a | n/a | bounded observation |
| `workspace_write` | rooted/scoped write | no common ExpectedEffect re-read path | no | no | bounded direct write; do not describe as full Control Plane assurance |
| `web_open` | bounded Browser schema/network policy | yes | no durable cross-call attempt settlement | no task Finish Gate | verified transition path |
| `web_interact` | bounded click/type + declared postcondition | yes | no durable cross-call WorkingState/reconciliation path | no task Finish Gate | verified transition path; delivery ambiguity fails closed for that call |
| `verified_workspace_artifact_v1` | closed registered procedure | yes | yes: WorkingState/AttemptIntent/reconciliation/LoopGuard scope | yes | current strongest general consequence/recovery reference path |
| `windows_case_update_v1` | closed registered candidate procedure | yes | procedure checkpoint/budget, but not the full WorkingState attempt/reconciliation model | external L3 Finish Gate required | strong transition verification with narrower recovery semantics |
| `chatgpt-temporary` Delegation | specialized bounded worker authority | provider-specific correlated delivery/result checks | yes: specialized durable launch/delivery/result settlement and no blind second Send | worker result explicitly != manager task DONE | strong specialized session/delegation path, not a universal runtime |

This table is a **depth map, not an acceptance downgrade**. Existing accepted scopes remain accepted for what their evidence proved. It prevents future architecture prose from silently upgrading a narrower path into guarantees it does not yet implement.

In particular:

- `workspace_write` is a useful bounded primitive but must not be cited as proof that all public mutations already pass through ExpectedEffect + WorkingState + Finish Gate;
- Browser currently has strong before/action/after verification but its ordinary public calls do not by themselves provide durable cross-call ambiguous-outcome reconciliation;
- `verified_workspace_artifact_v1` is the current reference implementation for durable logical operation / attempt / reconciliation semantics;
- Windows application procedure evidence proves a strong bounded workflow but its recovery model is not yet identical to the accepted WorkingState production consumer;
- Delegation correctly keeps a provider-specific durable lifecycle rather than pretending Chat sessions and file mutations are one state machine.

### Provider conformance rule

A new substrate is not accepted because it has a sandbox, policy engine, audit log, browser, shell, session store or "success" receipt. Before promotion, map the exact proposed role to the assurance layers above and prove the required properties.

Required review shape:

```text
proposed provider role
 -> exact consequence classes exposed
 -> exact bypass-capable native powers
 -> required assurance layers A..J
 -> provider-native guarantees
 -> thin CAP adapter responsibilities
 -> unresolved gaps
 -> deterministic/adversarial tests
 -> physical/L3 evidence where the consequence requires it
 -> PROCEED | NARROW | DEFER | REJECT
```

This applies equally to CCCC, WinApp CLI, UFO/UFO², OpenAdapt, OpenBot-style computer environments, Home Assistant and future candidates.

For sandbox/computer providers specifically, distinguish **environment lifecycle** from action authority:

```text
ExecutionEnvironment provider
   create / isolate / suspend / resume / destroy
            !=
Browser / Files / LocalExecution consequence authority
```

A reusable computer sandbox may be valuable without granting its resident agent unrestricted shell, filesystem or browser mutation authority. If the upstream environment exposes such powers, the qualified CAP profile must physically remove/deny them or place them behind separately accepted consequence contracts. Prompt-only discouragement is insufficient.

### Architecture completion target

The goal is **not** to force every path through one giant runtime. The goal is to make the assurance depth explicit and converge consequence-bearing paths on common guarantees where their failure model requires them:

```text
shared CAP invariants
      +
capability-native state
      +
provider-specific mechanics
      +
only the durable settlement machinery justified by that consequence class
```

This keeps composition-first honest: reuse mechanics aggressively, but never outsource CAP's authority, effect verification, ambiguity handling or completion semantics by accident.

---

## 3. What CAP should stop building by default

After #149, do **not** start or continue broad project-owned implementations of the following merely because they are useful agent-platform features:

```text
generic daemon/supervisor
generic persistent actor/session registry
generic durable messaging/inbox
generic delivery ledger for every provider
generic persistent conversation manager
generic agent-to-agent routing
generic scheduler / heartbeat / goals runtime
generic retained-worker runtime
generic subagent manager

generic Windows UIA engine
generic Windows selector engine
generic mouse/keyboard backend
generic screenshot/window manager
per-application CAP adapters by default
per-site / per-web-app CAP adapters by default

own demonstration recorder
own general workflow compiler/replay engine

own IoT device registry
own Matter controller
own MQTT integration framework
vendor-by-vendor IoT integrations by default
```

A custom implementation of one of these requires a **measured gap**: a concrete consumer, a failed/rejected reuse candidate, and Stage Research showing why the project-owned implementation is the smallest justified mechanism.


### Future shared-memory multi-agent research

A promising future research direction is to test whether several strong agents can coordinate through a controlled persistent shared-knowledge space without CAP hard-coding a large planner/worker/reviewer hierarchy.

The hypothesis is:

```text
multiple strong agents
+ persistent shared knowledge
+ ability to continue / challenge / extend prior work
=
emergent collaboration
+ specialization
+ cross-run continuity
+ accumulated long-horizon progress
```

The shared-memory layer would support exploration, handoff, synthesis and spontaneous division of labor. CAP would remain the separate authority/effect layer for consequential actions, fresh verification and whole-task completion.

This remains research-only and does not authorize a swarm runtime or project-owned multi-agent infrastructure.

See: `SHARED_MEMORY_MULTI_AGENT_ARCHITECTURE.md`.


---

## 4. Provider families — narrow contracts, not one universal state machine

Do not invent a universal `ExecutionProvider` state machine that flattens ChatGPT conversations, Windows application state, browser pages and physical devices.

Prefer separate narrow provider families with shared CAP invariants above them:

```text
SessionProvider
DesktopProvider
BrowserProvider
ProcedureProvider
DeviceProvider
```

Common CAP-level obligations may include:

```text
subject/target identity
logical operation identity
provider receipt/evidence identity
consequence authority boundary
ambiguous outcome handling
fresh observation
reconciliation
provenance
wrong/foreign target rejection
replay/duplicate rejection where applicable
```

Provider-native state remains provider-native when flattening it would lose useful semantics.

The adapter conformance suite is an **acceptance layer first**, not authority to merge every adapter into one runtime/state machine.

### Planner / executor separation reference — codex-with-chatgpt

External architecture reference:

- repository: `XiaoDuoYa/codex-with-chatgpt`
- inspected `main` baseline on 2026-09-14: `9663b88753e35c76796c5bce000293e0bd22cd9e`
- license: MIT
- CAP disposition: **REFERENCE_ONLY / ADAPT_MECHANIC** by default

This project is relevant because it demonstrates a narrow composition in which ordinary ChatGPT acts as planning/review layer while Codex owns mutation/execution. Its architecture separates two channels:

```text
                 ChatGPT
                    |
          +---------+---------+
          |                   |
          v                   v
   control messages       read-only MCP
          |                   |
          v                   v
        Codex              workspace
          |
          v
 shell / files / git / tests
```

The useful CAP lesson is not the fixed `ChatGPT <-> Codex` product pairing. It is the stronger boundary:

```text
planner / reviewer
        !=
mutation executor
        !=
verification authority
```

and the related separation:

```text
control plane
        !=
data/evidence plane
```

The inspected protocol uses concise state-bearing control messages while current files, diffs, git state and released execution output are read independently through the workspace connector. The reviewer is explicitly instructed not to accept an executor's `EXECUTED` claim as proof; it re-reads the diff/evidence before returning another plan or `DONE`.

That mechanic aligns with CAP's existing distinction:

```text
provider execution/result
        !=
freshly verified external effect
        !=
whole-task completion
```

#### Mechanics worth Stage Research

Research for selective adaptation:

- physically read-only planner/reviewer workspace access;
- narrow control messages separate from code/diff/log payloads;
- explicit task/iteration identity;
- independent post-execution inspection rather than trusting executor summaries;
- bounded handoff/checkpoint state when a planning conversation is replaced;
- workspace-scoped connector identity and wrong-workspace rejection;
- execution-output release as evidence rather than ambient unrestricted shell access;
- recovery/iteration limits that do not imply blind replay of consequential mutations.

The upstream protocol's `INIT / PLAN / EXECUTED / DONE / BLOCKED / HANDOFF` style states are useful reference mechanics, but CAP must not adopt them as a second universal state machine if existing CAP operation/attempt/WorkingState semantics already cover the needed identity and settlement behavior.

#### CAP adaptation hypothesis

A provider-neutral form to evaluate is:

```text
strong planner/reviewer
        |
        v
CAP trust / authority / correlation / verification
        |
        +----------------------+
        |                      |
        v                      v
read-only evidence         execution provider
surface                    (Codex / other)
        |                      |
        v                      v
workspace state       files / shell / git / tests
        \______________________/
                   |
                   v
            fresh CAP review
```

The planner identity and executor identity should remain replaceable. Do not hard-code `ChatGPT -> Codex` as the CAP architecture and do not make Cloudflare Tunnel, this project's MCP server, or its browser-control path mandatory dependencies.

#### Questions before any reuse

1. Which read-only workspace tools materially improve independent verification over CAP's current evidence paths?
2. Which security properties are structural (no write/shell tools exposed) versus prompt-only?
3. Can the connector be used without giving the planning model a parallel consequence-bearing authority path?
4. How should CAP map task/iteration/handoff identifiers onto canonical operation/attempt/session identities without duplicating them?
5. Which control-plane messages are actually needed once CAP already owns WorkingState and Finish Gate?
6. Can execution output be exposed as bounded evidence with provenance and retention rules rather than a general data channel?
7. Which tunnel/authentication mechanics are needed only because the planner runs in cloud ChatGPT, and which should remain provider-specific?
8. How does the design behave after ambiguous executor crash, partial mutation or lost control message?
9. Can wrong-workspace/cross-project connector use be rejected deterministically at the CAP boundary?
10. Which mechanics are useful independently of Codex and ordinary ChatGPT so they remain valuable with future providers?

---

## 5. Sessions — CCCC first, #149 specialized, Prime optional

### 5.1 PR #149

PR #149 is **accepted and merged**. Preserve its current narrow scope rather than broadening the specialized Temporary Chat implementation.

Its role is the specialized isolated profile:

```text
fresh
independent
non-personalized
no-plugin
Temporary Chat
one-shot bounded worker
```

Do not generalize #149 into the persistent-session runtime.

### 5.2 Persistent ordinary ChatGPT

For persistent ordinary-ChatGPT conversation/session delivery, the **first candidate** remains CCCC or an equivalent mature substrate discovered by fresh research.

Target role:

```text
one persistent ordinary ChatGPT conversation
+ explicit target binding
+ deterministic delivery identity/receipt
+ crash/ambiguous-delivery settlement
+ no blind resend
+ browser delivery / wake mechanics
```

CAP should own the logical request/session identity and treat the substrate's delivery identity as provider evidence rather than making provider identity the canonical CAP identity.

Conceptual seam:

```text
CAP model_request_id / session_ref
            |
            v
      SessionProvider adapter
            |
            +--> provider delivery_id / receipt / status
            |
            v
      ordinary ChatGPT conversation
```

### 5.3 Mandatory CCCC authority gate

Before adopting CCCC Web Model as a production session provider, prove that the selected profile cannot bypass CAP consequence authority through direct shell/git/repo-edit/write/code-execution powers.

Required question:

> Can the persistent ChatGPT actor be made **transport/session-only** (plus the bounded CAP semantic surface), with mutation authority outside CAP physically unavailable rather than merely discouraged by prompt?

If current CCCC cannot satisfy this directly, first evaluate the smallest config/profile/upstream contribution/fork needed to create a transport-only profile. Do not respond by rebuilding the entire persistent-session runtime locally unless that route is proven impractical.

### 5.4 Prime

Prime is **not on the critical path for basic persistent ChatGPT**.

Prime remains an optional candidate only when a concrete missing primitive is observed, such as:

```text
persistent local Python/IPython/kernel state
retained compute workers
subagent runtime
context compaction runtime
long-running local agent loop
scheduler/heartbeat mechanics that a real consumer requires
```

If needed, Prime should remain behind a narrow adapter. Do not make Prime the mandatory heart of CAP merely to obtain persistent ordinary-ChatGPT turns.

The existing Prime roadmap/addendum remain useful **candidate-specific research input**, but this composition-first document supersedes their Prime-first sequencing as the intended post-#149 starting point.

---

## 6. Desktop / Windows — generic Windows automation first

Do not continue toward a broad custom Windows automation engine and do not create one CAP adapter per installed application by default.

An installed Windows program — CAD, Office, Electron, Win32/WPF/WinForms or another desktop application — should normally enter through the same Desktop capability. CAP should first rely on reusable Windows/application automation substrates; app-specific mechanics belong inside those substrates where possible.

Preferred routing hypothesis for fresh Stage Research:

```text
installed Windows application
        |
        v
1. WinApp CLI / UI Automation semantic automation
        | unavailable / insufficient
2. UFO/UFO² or another qualified reusable
   application-aware Windows automation layer
        | unavailable / insufficient
3. structured GUI + synthetic input
        | insufficient
4. selective vision grounding
```

### Generic Windows substrate candidate

Microsoft WinApp CLI is the first candidate for generic Windows UI mechanics such as inspection, semantic targeting, UIA pattern actions, waiting, screenshots and input fallback.

The desired user experience is that installing or opening another ordinary Windows application does **not** imply new CAP development. The generic Desktop path should attempt to observe, target, act and verify through the reusable Windows substrate first.

CAP must still own:

```text
authorization
stable subject/operation identity
ExpectedEffect
fresh post-action observation
PASS | FAIL | UNKNOWN
reconciliation
Finish Gate
```

A successful WinApp/UIA invocation is action evidence, not proof of the desired effect.

### Application-aware mechanics and UFO/UFO²

If generic WinApp/UIA semantics are insufficient for a complex application, the next preferred move is a qualified reusable application-aware Windows layer such as UFO/UFO², **not** a new CAP-native adapter for that product.

UFO/UFO² may internally use richer UIA/Win32/WinCOM/application-specific/native mechanics where useful. Those mechanics remain implementation details of the reusable executor unless fresh Stage Research proves a concrete capability gap that cannot be solved there.

Do not adopt UFO HostAgent/AppAgent planner hierarchy as the CAP planner. Ordinary ChatGPT remains the general planner; CAP keeps authority/effect/verification semantics.

Example principle:

```text
CAP
  -> DesktopProvider
      -> WinApp CLI first
      -> UFO/UFO² when application-aware mechanics are needed
          -> may internally use COM/native APIs if that executor supports them
```

Avoid the default pattern:

```text
CAP
  -> AutoCADProvider
  -> SolidWorksProvider
  -> ExcelProvider
  -> WordProvider
  -> PhotoshopProvider
  -> ...
```

A direct app-specific CAP adapter is an exception requiring a measured gap and fresh Stage Research, not the normal expansion path.

Universal App Bridge or similar routing projects may be compared as reuse candidates, but are not preselected as the CAP foundation.

---

## 7. Browser — generic browser automation first

Browser already has an accepted project semantic boundary and Playwright-based execution path. Keep that boundary; do not replace it for architectural symmetry.

A web application should normally be treated as another target behind `BrowserProvider`, not as a new CAP capability family or a mandatory product-specific integration.

Preferred routing rule:

```text
web application / site
        |
        v
1. existing Playwright/project Browser path
   DOM / accessibility / semantic targeting
        | unavailable / insufficient
2. qualified reusable site-aware browser mechanics
        | unavailable / insufficient
3. narrow site-specific Browser adapter for a measured gap
        | insufficient
4. selective visual/coordinate fallback where separately allowed
```

The desired user experience is that opening another ordinary web application does **not** imply new CAP development. Figma, Google Sheets, Notion, Canva, CRM/ERP systems and similar browser products should first be attempted through the generic Browser path.

Do not default to:

```text
FigmaProvider
GoogleSheetsProvider
NotionProvider
CanvaProvider
SalesforceProvider
...
```

If a specific site has a repeatable structural problem — for example virtualization, canvas-heavy interaction, unusual shadow DOM or another mechanism that the generic path cannot handle reliably — first prefer a reusable browser-layer solution. A direct site-specific CAP Browser adapter is the last implementation step and requires a measured gap plus the applicable fresh Stage Research.

CAP still owns target identity, consequence authorization, provenance, ExpectedEffect, fresh post-action observation, ambiguous-outcome handling, reconciliation and Finish Gate. A successful Playwright click/type/navigation is action evidence, not proof of the required task effect.

Future Browser changes should therefore be measured-gap driven and preserve the current accepted Browser authority/verification boundary.

---

## 8. Demonstration / procedures — OpenAdapt first

Do not build a project-owned recorder/compiler/replay stack by default.

Preferred existing seam remains:

```text
human demonstration
 -> OpenAdapt Capture
 -> Flow / ProgramGraph compile
 -> deterministic replay/checkpoint where qualified
 -> upstream execution/effect evidence
 -> CAP observation/evidence adapter
 -> CAP ExpectedEffect
 -> CAP Verification Kernel
 -> CAP Finish Gate
```

One successful demonstration creates at most a candidate procedure/skill. Upstream replay success does not automatically become CAP `PASS`/`DONE`.

---

## 9. IoT / physical devices — preserve the existing Home Assistant-first decision

The existing IoT Stage Research remains authoritative for production status: IoT production adoption is still deferred until fresh re-entry with a concrete device/user scope.

The intended composition direction is preserved:

```text
CAP DeviceProvider
        |
        v
Home Assistant preferred first candidate
        |
        +--> Matter
        +--> MQTT
        +--> Zigbee / Z-Wave / Bluetooth
        +--> vendor integrations
```

Do not build direct Matter/MQTT/vendor stacks unless a measured requirement cannot be satisfied through the preferred aggregator path.

Core invariant:

```text
backend accepted command
        !=
backend observed state change
        !=
required physical effect proven
```

CAP owns consequence policy, stable subject identity/provenance, fresh observation, ExpectedEffect, reconciliation and Finish Gate. Safety-critical/hazardous control remains below LLM final authority and requires deterministic/device-specific interlocks.

---

## 10. Post-#149 order — speed-first sequence

PR #149 is already accepted and merged. The active sequence is:

```text
#149 accepted + merged
        |
        v
composition-first research branch active
        |
        v
rerun repository skill/bootstrap context as needed
        |
        v
Composition Stage Research
        |
        +--> Sessions: CCCC first candidate
        |      -> transport-only authority gate
        |      -> persistent multi-turn proof
        |      -> crash / ambiguous / wrong-target conformance
        |
        +--> Desktop: WinApp CLI first candidate
        |      -> generic DesktopProvider proof
        |      -> UFO/UFO² only for measured application-aware gaps
        |      -> 3-4 representative app L3 matrix without per-app CAP adapters
        |
        +--> Browser: preserve accepted Playwright generic path
        |      -> no per-site CAP adapter by default
        |      -> specialize only after a measured repeatable web-app gap
        |
        +--> Procedures: revalidate OpenAdapt selected roles
        |      -> bounded demo/compile/replay spike
        |
        +--> IoT: preserve DEFER; revalidate Home Assistant only
        |      when a concrete device consumer is actually scheduled
        |
        v
adapter conformance obligations
        |
        v
implement only thin adapters + CAP-owned remainder
        |
        v
custom code only for measured gaps
```

Prime Stage Research moves off the mandatory path. Run it only if the CCCC/session proof or a later concrete consumer demonstrates a missing runtime primitive that Prime may solve.

IoT remains off the immediate release-critical path unless the roadmap is separately changed by accepted Stage Research.

---

## 11. Composition Stage acceptance questions

### Sessions / CCCC

1. Can one persistent ordinary ChatGPT conversation survive multiple delivered turns with exact target binding?
2. Can crash/claimed/ambiguous outcomes reconcile without blind resend?
3. Can the actor be restricted to transport/session mechanics plus bounded CAP tools, with shell/git/repo-edit/code-exec mutation routes physically unavailable?
4. Can CAP retain canonical request/session identity while treating CCCC delivery state as provider evidence?
5. Does the adapter survive wrong conversation, stale generation, replayed result and duplicate delivery tests?

### Desktop / WinApp CLI + UFO/UFO²

1. Does WinApp CLI provide strong enough structured identity/targeting for representative Win32/WPF/WinForms/Electron and complex installed applications?
2. How stable are selectors/slugs across restart, moved windows and similar controls?
3. Can a newly installed application be controlled through the generic Desktop path without adding a new CAP adapter?
4. When WinApp/UIA is insufficient, can UFO/UFO² or another reusable application-aware layer supply the missing mechanics while CAP remains the planner/authority/verification owner?
5. Do native/COM/application-specific mechanics, when useful, remain internal to the reusable executor instead of becoming a default CAP integration surface?
6. Does post-action CAP re-observation prove effects independently of executor command success?
7. Which measured gaps, if any, truly justify a direct specialized CAP adapter?

### Browser / Playwright + measured specialization

1. Can a newly encountered ordinary web application be controlled through the existing generic Browser path without adding a new CAP adapter?
2. Do DOM/accessibility/semantic target identities remain strong enough across reload, navigation, dynamic updates and similar elements?
3. When a web application uses virtualization, canvas, shadow DOM or another difficult structure, can a reusable browser-layer mechanism solve the problem before introducing site-specific CAP code?
4. Does fresh post-action observation prove the intended effect independently of Playwright command success?
5. Which measured repeatable gaps, if any, truly justify a direct `FigmaWebAdapter`, `GoogleSheetsWebAdapter` or other site-specific Browser adapter?
6. Can any site-specific mechanics remain below the existing CAP Browser authority/provenance/verification boundary rather than becoming new planner or completion authority?

### Procedures / OpenAdapt

1. Can capture/compile/replay be reused without importing planner/completion authority?
2. Can CAP preserve current WorkingState/ExpectedEffect/Verification semantics above it?
3. Does one bounded real workflow eliminate enough local code to justify adoption?

### IoT / Home Assistant

Only on future concrete re-entry:

1. Can stable registry/device identity safely bind CAP SubjectRef?
2. Are state/event observations fresh and strong enough for the selected effect class?
3. How are assumed/unavailable states treated?
4. How are ambiguous physical outcomes reconciled without unsafe blind retry?
5. What consequence classes require stronger interlocks than CAP's normal authorization/verification loop?

---

## 12. Decision rule: reuse before build

For every proposed post-#149 mechanism:

```text
needed capability
 -> existing accepted/researched substrate?
 -> credible mature external component?
 -> narrow adapter possible?
 -> conformance/failure test
 -> measured gap?
      no  -> reuse/adapt
      yes -> smallest custom mechanism for that exact gap
```

Do not write generic infrastructure first and ask whether it was necessary later.

A component being fashionable/new is not enough to adopt it. Conversely, CAP having an old prototype is not enough reason to keep expanding it when a maintained upstream component now provides the mechanical layer more cheaply.

---

## 13. Scope lock

Until fresh Stage Research changes this direction, treat the following as the intended post-#149 architectural boundary:

```text
CAP = trusted composition kernel
      + narrow provider adapters
      + provider conformance / physical acceptance

not

CAP = project-owned implementation of every agent/session/desktop/procedure/IoT runtime
```

The project's distinctive value is the stable trust/effect semantics over replaceable executors:

```text
Who/what is the exact target?
Was this consequence authorized?
What exact logical operation is this?
Could a prior attempt already have applied?
What evidence is fresh and provenance-bound?
Did the intended effect actually happen?
Is the whole task done, or only one transition?
```

That boundary should be preserved even when the mechanical executor underneath changes.

---

## 14. Workspace extraction decision — source-backed Stage Research

Research performed 2026-09-15, recorded 2026-09-16. This is a bounded decision
about extracting `WorkspaceProvider`, not completion of the Sessions/Desktop
research in this Draft. It does not adopt any new production dependency.

### Goal and exact baseline

Determine whether the accepted local-file path needs an execution-only provider
now, and identify which responsibilities must stay in CAP. CAP source inspected:
`92ef431b9d412bd78307c51641b1379184fe560d` (accepted main after #157).
The research branch was refreshed from that main; runtime and tests are identical
to it. The CURRENT_STATE merge conflict was resolved using the accepted main
owner so #157's evidence limitations and reviewer fallback are preserved.

The candidate must preserve rooted scope, exclusive creation, object identity,
prepared intent before effect, no blind retry, independent observation, and CAP
Verification Kernel/Finish Gate decisions. A new class name is not a product
outcome. No second filesystem backend requiring substitution was identified in
the inspected procedure call sites.

### Problem evidence: the actual two paths

| Current path | Executable owner / trace | Contract and extraction consequence |
|---|---|---|
| `workspace_write` | `runtime/semantic-projection/bin/semantic-control-plane-projection.mjs` forwards to `semantic-projection.mjs`; its handler resolves the relative workspace path and calls filesystem backend `write_file` | Bounded create-or-overwrite, not this procedure's durable no-overwrite graph. A filesystem execution backend already exists here. Reusing its write verb would change the procedure's semantics. |
| `procedure_run` / `verified_workspace_artifact_v1` | semantic projection -> `runtime/control_plane/cli.py::_run_workspace_artifact` -> package initialization -> `verified_workspace_artifact.py::run_verified_workspace_artifact` | CAP admission, request validation, task correlation/lock, checkpoint recovery and graph execution. This whole function is not an execution-only provider. |
| Stage creation | `_prepare_transition` -> durable checkpoint -> patched `_exclusive_create_file` -> fresh observation -> Kernel -> receipt/checkpoint | `control_plane/__init__.py` installs handle-relative Windows creation, live delivery proof and checkpoint wrappers before the procedure uses them. Creation proof survives the call return until its receipt is durable. |
| Final creation | `pin_file_for_verified_link` -> retained identity/content checks -> `_exclusive_link_file` -> AFTER/Kernel -> checkpoint within the pin | Same-filesystem hard link, no overwrite. Returning from a narrow link call must not release the surrounding protection early. |
| Cleanup / compensation | `pin_file_for_verified_delete` and `VerifiedDeletePin`; independent final observation and Finish Gate | Handle-bound deletion revalidates identity. Compensation is blocked while an attempt is unresolved and may delete only a verified owned object. |

Targeted searches covered `WorkspaceProvider`, `workspace_provider`, provider
directories, `run_verified_workspace_artifact`, `_exclusive_create_file`,
`_exclusive_link_file`, checkpoint writers and their call sites in runtime/tests.
No existing separate WorkspaceProvider was found there. This is a bounded search
result, not a claim that all future backends are unnecessary.

Concrete failure history is executable in
`test_stage26_3c_post_effect_exception_recovery.py`,
`test_stage26_3c_checkpoint_progress_validation.py`,
`test_stage26_3c_stage_create_namespace_pin.py` and the workspace hard-crash,
link-pin, delete-pin and reconciliation-authority suites. In particular,
post-link verification/checkpoint exceptions retain the last prepared state so
resume reconciles rather than creating another link. Matching bytes alone must
not manufacture ownership after loss of the process-local creation proof.

### Primitives and engineering domains

| Primitive | Domain / required boundary |
|---|---|
| Exclusive create and same-volume link | Filesystem namespace atomicity; collision cannot overwrite an existing target |
| Open file/directory handles and generation identity | OS object lifetime, reparse/TOCTOU/ABA protection; a path string is not retained object identity |
| Prepared intent, atomic checkpoint replacement and lock | Recovery/transaction processing and cooperating-writer serialization; process-restart scope, not a machine-power-loss transaction |
| Independent AFTER evidence and reconciliation | Controller/verification semantics; delivery receipts cannot award PASS or authorize retry |
| Context lifetime through durable receipt | Resource ownership; executor-return and proof-release are distinct boundaries |

Microsoft's [CreateFileW contract](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
explains handle sharing restrictions; [NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile)
allows a leaf to be resolved relative to an open directory handle. This supports
the existing CAP namespace mechanism, not a generic path-only replacement.
[CreateHardLinkW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createhardlinkw)
requires links to stay on one volume. A fallback copy/move is a different effect.

### Source-code evidence and external failure lessons

- **CAP, exact main above — OPEN_IMPLEMENTED / KEEP.** Traced projection, CLI,
  package import bindings, procedure, support helpers, observation and Windows
  pins. `__init__.py::_write_checkpoint_with_recovery_and_stage_create_proof`
  preserves the last durable prepared state and releases proof only after a
  successful checkpoint. The wrapper's finally cleans up on exit. Reading the
  procedure module in isolation would miss these production semantics.
- **fsspec/filesystem_spec at `d548583843a2400b1f47318d5efd03b4b59d711e` —
  OPEN_IMPLEMENTED / REFERENCE_ONLY.** Inspected
  [Transaction.complete](https://github.com/fsspec/filesystem_spec/blob/d548583843a2400b1f47318d5efd03b4b59d711e/fsspec/transaction.py),
  `LocalFileSystem.link`, `LocalFileOpener._open/commit/discard`, and local tests
  `test_commit_discard`, `test_transaction_ends_when_a_commit_fails` and
  `test_transaction_cross_device_but_mock_temp_dir_on_wrong_device`. Commit loops
  over files and local publication uses `shutil.move`; failed completion cleans
  up remaining deferred files and resets transaction state. A local probe using
  these exact classes confirmed overwrite of an existing file and a partial
  commit when the second file's commit raises: `a=true, b=false, c=false`, with
  transaction state reset. This is not CAP no-overwrite or durable reconciliation.
  Upstream regression comments describe cached instances swallowing later writes
  when failed transactions were not reset. CAP must keep outcome reconciliation
  distinct from resource cleanup. No fsspec dependency is selected.
- **OpenAdaptAI/openadapt-flow at `cfea6ecd9540b78bafcdf6bb72887d61c2a59fc0` —
  OPEN_IMPLEMENTED for inspected durable workflow mechanics / REFERENCE_ONLY
  for this extraction.** Inspected
  [checkpoint.py](https://github.com/OpenAdaptAI/openadapt-flow/blob/cfea6ecd9540b78bafcdf6bb72887d61c2a59fc0/openadapt_flow/runtime/durable/checkpoint.py),
  `DurableController.record` and `durable/resume.py`: workflow results are
  evidence-checked before checkpoint publication, writes use sibling temporary
  files plus fsync/replace, and resume validates retained manifest, pause and
  inputs. Read tests for projection failure and exact resume-state binding in
  `test_durable_runtime.py` and `test_durable_resume_state_binding.py`; not executed
  here. This is a workflow persistence/authority subsystem, not a drop-in local
  file executor. Its current source differs from CAP's existing Flow lock; no
  version update or wholesale reuse is justified by this narrow question.

The fsspec probe used temporary files and `unittest.mock.patch` on
`LocalFileOpener.commit`, raising `PermissionError` for basename `b` while
committing files `a,b,c`. Expected observed output:
`existing_after=new; a=true; b=false; c=false; transaction_reset=true`.
The upstream pytest suite was not run because pytest is absent in this runtime.

### Alternatives and lineage comparison

| Approach | Owner / recovery and identity | Benefit / limitation | Decision for this question |
|---|---|---|---|
| Keep accepted procedure and existing OS helpers | CAP owns intent/state/verification; handles span consequence and receipt | Proven scoped boundary, no new dispatch; import-time wiring remains a maintenance cost | Selected now |
| Extract a local execution-only context adapter | CAP must still own all decisions; adapter retains handles until CAP finishes observation/checkpoint | Potentially clearer mechanical dependency, but a simple `execute -> receipt` API is insufficient; no present substitution consumer proves the extra abstraction | Defer until a concrete consumer and lifetime conformance proof |
| Replace file primitives with general filesystem API / fsspec transactions | Library owns publication mechanics; CAP still needs separate identity/recovery | Useful backend breadth, but inspected transaction semantics allow overwrite/partial commit and do not supply CAP pin lifetimes | Reject as a drop-in replacement, not as a future library in another scope |
| Reuse OpenAdapt procedure runtime | External workflow has its own durable state, evidence and continuation rules | Relevant to future compiled procedures; adopting it here changes more than a file-execution boundary | Keep prior future role; no adoption in this slice |

Baseline roles `capability authorization`, `capability-spanning WorkingState`,
`transition verification`, and `task completion`: **KEEP** project ownership.
OpenAdapt compiler, checkpoint/resume and effect-evidence roles: **KEEP** their
existing revalidate-per-consumer selection; this investigation does not replace
them or claim to qualify a new integration. A generic WorkspaceProvider registry
would be **NEW_ARCHITECTURE**, not an already accepted baseline requirement.
No existing role assignment changes, so the reuse baseline is not rewritten.

### Failure/crash matrix constraining any later extraction

| Boundary | Retained / possible physical state | Required evidence; permitted extra effects | Existing guard / acceptance obligation |
|---|---|---|---|
| Before intent checkpoint | No delivery authorized | Zero effects until CAP durably prepares | `_prepare_transition`, budget/admission tests |
| Prepared, before create | Intent; file absent or foreign file appears | Fresh observation; retry only after confirmed-not-applied, within budget | working-state/reconciliation suites |
| Create applied, receipt absent | Prepared intent; staging may exist | Live creation proof required to adopt; after complete process loss matching bytes alone stay UNKNOWN, zero blind adoption | stage-create namespace/proof and hard-crash suites |
| Final link applied, receipt/checkpoint fails | Last prepared state; staging and target may refer to the same retained object | Fresh same-stream identity/Kernel proof; no second link when applied | post-effect-exception and hard-crash suites |
| Receipt durable, before next node | Verified prior action | Validate checkpoint progress against WorkingState; zero replay of settled action | checkpoint-progress-validation suite |
| Cleanup effect / acknowledgement ambiguous | Prepared cleanup; staging may be absent | Reobserve target identity and staging absence; no blind second delete | hard-crash and reconciliation suites |
| Checkpoint write fails | Last durable prepared state remains authoritative | Preserve it; no terminal failure overwrite that erases recovery | checkpoint recovery wrapper and regression tests |
| Concurrent resume / foreign same-content replacement | One task lock; identity may diverge | Loser cannot act; content equality does not authorize replacement | task lock, identity, pin suites |
| Compensation during unresolved attempt | Outcome unsettled | Zero compensation until settled; delete only verified owned object | `safe_to_compensate`, delete-pin and normal-authority suites |

These are existing design obligations, not claims that Linux reproduces Windows
handle protection. The attempted Linux/Python 3.12 run of six relevant modules
reported **45 tests: 19 failures, 2 errors, 2 skipped**. A minimal real procedure
probe stopped at `staged_verified` with `delivery_error_confirmed_not_applied`;
Windows pin APIs explicitly reject non-Windows execution. Runtime/tests have no
delta from the accepted main in this branch. This local run is not acceptance;
use exact-head hosted Windows CI for the supported implementation. It does not
justify weakening pins or introducing portable fallback writes.

### Decision, verification and re-entry

**DEFER production WorkspaceProvider extraction.** Keep the accepted execution
path. The whole procedure owns CAP trust/recovery and cannot become a provider;
a new path-only wrapper adds no current capability and risks shortening proof
lifetime. This is a completed negative decision for this candidate, not approval
of all remaining PR #151 research.

Re-enter when a concrete second backend or bounded consumer demonstrates which
mechanics must vary. Before implementation, specify retained-object lifetime,
exclusive publication, exception-after-effect handling, independent observation
and checkpoint ownership; prove the matrix on the supported Windows path. Then
obtain a fresh PROCEED/NARROW decision, independent semantic review and applicable
physical qualification. Generic remote storage, machine-power-loss durability,
agent/session runtimes and broad provider registries are outside this decision.

Complexity budget: no new runtime class, registry, state store, tool, dependency
or documentation owner. This section uses the existing composition research
owner and replaces the unsupported assumption that renaming the procedure
constitutes provider separation. Production implementation remains blocked for
this extraction until the stated re-entry conditions are met.
