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
 Prime optional            native app APIs        Matter/MQTT via HA
                           OpenAdapt
                           Vision fallback

Browser remains a separate accepted capability path using the current
Playwright/project Browser boundary unless fresh evidence justifies change.
```

This is a **composition architecture**, not a plan to collapse all providers into one universal runtime.

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

own demonstration recorder
own general workflow compiler/replay engine

own IoT device registry
own Matter controller
own MQTT integration framework
vendor-by-vendor IoT integrations by default
```

A custom implementation of one of these requires a **measured gap**: a concrete consumer, a failed/rejected reuse candidate, and Stage Research showing why the project-owned implementation is the smallest justified mechanism.

---

## 4. Provider families — narrow contracts, not one universal state machine

Do not invent a universal `ExecutionProvider` state machine that flattens ChatGPT conversations, Excel cells, browser pages and physical devices.

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

---

## 5. Sessions — CCCC first, #149 specialized, Prime optional

### 5.1 PR #149

PR #149 remains valuable and must be completed under its current narrow scope.

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

After #149 merge, the **first candidate** for persistent ordinary-ChatGPT conversation/session delivery is CCCC or an equivalent mature substrate discovered by fresh research.

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

## 6. Desktop / Windows — WinApp CLI first, native semantics where stronger

Do not continue toward a broad custom Windows automation engine by default.

Preferred routing hypothesis for fresh Stage Research:

```text
1. application-native semantic API
        | unavailable / insufficient
2. WinApp CLI / UI Automation semantic patterns
        | unavailable / insufficient
3. structured GUI + synthetic input
        | insufficient
4. selective vision grounding
```

### Generic Windows substrate candidate

Microsoft WinApp CLI is the first candidate for generic Windows UI mechanics such as inspection, semantic targeting, UIA pattern actions, waiting, screenshots and input fallback.

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

### Office / richer applications

When a native object model provides stronger identity and semantics than UIA, prefer a narrow native adapter.

Example:

```text
Excel workbook / worksheet / Range("D17") / Formula
```

is preferable to coordinate-based editing when the native model is available and qualified.

UFO/UFO² remain candidate sources of application-specific UIA/Win32/WinCOM mechanics for measured gaps. Do not adopt their planner hierarchy as the CAP planner.

Universal App Bridge or similar routing projects may be compared as reuse candidates, but are not preselected as the CAP foundation.

---

## 7. Browser — keep the accepted Playwright boundary

Browser already has an accepted project semantic boundary and Playwright-based execution path.

Do not replace it for architectural symmetry.

Future Browser changes should be measured-gap driven and preserve project-owned identity, provenance, consequence policy, observation/effect verification and Finish Gate semantics.

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

After PR #149 is accepted and merged:

```text
#149 accepted + merged
        |
        v
refresh this research branch from new main
        |
        v
rerun repository skill bootstrap
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
        |      -> narrow CAP adapter proof
        |      -> 3-4 representative app L3 matrix
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

## 11. First acceptance questions after #149

### Sessions / CCCC

1. Can one persistent ordinary ChatGPT conversation survive multiple delivered turns with exact target binding?
2. Can crash/claimed/ambiguous outcomes reconcile without blind resend?
3. Can the actor be restricted to transport/session mechanics plus bounded CAP tools, with shell/git/repo-edit/code-exec mutation routes physically unavailable?
4. Can CAP retain canonical request/session identity while treating CCCC delivery state as provider evidence?
5. Does the adapter survive wrong conversation, stale generation, replayed result and duplicate delivery tests?

### Desktop / WinApp CLI

1. Does it provide strong enough structured identity/targeting for representative Win32/WPF/WinForms/Electron apps?
2. How stable are selectors/slugs across restart, moved windows and similar controls?
3. Can native semantic APIs outrank generic UIA where they provide stronger object identity?
4. Does post-action CAP re-observation prove effects independently of WinApp command success?
5. Which measured gaps, if any, justify UFO/native/specialized adapters?

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
