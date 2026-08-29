# ChatGPT deep-link autosend bootstrap — Stage Research Brief

Date: 2026-08-29
Base: `main` at `61a8dfa6e5f4310760b1b605d706c09854ab6ebf`
Scope: experimental bootstrap only; no production scheduler/runtime authority.

## Stage question

Can the project wake a fresh **ordinary ChatGPT** worker without paid API usage or ChatGPT Work/Computer Use by opening a ChatGPT `?prompt=` deep link that already resolves `@Chat Local Bridge Test`, then performing only the missing Send action?

Observed physical problem evidence from the 2026-08-29 manual probe:

- `https://chatgpt.com/?prompt=...` opened a fresh ordinary **Chat** surface;
- `@Chat Local Bridge Test` resolved to the visible plugin chip;
- the remaining prompt text appeared in the composer;
- ChatGPT did **not** submit the prompt automatically.

The missing mechanism is therefore a bounded local submit action, not a replacement planner, MCP transport, or local executor.

## Durable invariants

- Ordinary ChatGPT remains the only current general planner.
- The accepted six-tool Chat semantic surface is unchanged.
- The extension must not call the Local Bridge, filesystem, shell, browser network APIs, Codex, Work, or any model API.
- It may act only on `https://chatgpt.com/*` and only after an explicit opt-in URL contract.
- It must verify the expected plugin chip and run id sentinel in the same composer before Send.
- Ambiguity, changed DOM, missing plugin, disabled Send, timeout, or repeated run id must fail closed with **no click**.
- One run id may cause at most one physical Send attempt per tab session.
- The run id is correlation/deduplication data, not a secret, credential, capability grant, or authorization token.
- The experiment does not grant task-completion, tool, or Control Plane authority.

## Current project truth / architecture lineage comparison

Affected prior roles from `ARCHITECTURE_REUSE_BASELINE.md`:

| Role | Prior boundary | Decision | Reason |
|---|---|---|---|
| General planning / novel strategy | ordinary ChatGPT | `KEEP` | The extension only wakes a fresh ordinary Chat turn; it performs no planning. |
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | `KEEP` | The extension does not replace MCP transport; the already attached Chat plugin continues using the accepted route. |
| Multi-chat / provider browser adaptation | CtxPort ideas + project Browser Companion direction | `DEFER` for this experiment | Cross-provider extraction/handoff is not required to prove one ChatGPT bootstrap. |
| Agent session / wake lifecycle | Codex reference-only; wake/scheduler semantics unresolved | `REFINE` only as an experimental wake candidate | This experiment tests a browser-host wake seam without adopting Codex runtime or changing project session authority. |
| Capability-spanning operational state | project WorkingState | `KEEP` | If this bootstrap later becomes a worker launcher, durable task state remains outside chat history. |
| Authorization / verification / Finish Gate | project-owned | `KEEP` | Autosend is not evidence of task success and grants no consequence authority. |

No accepted baseline role currently owns an ordinary-Chat deep-link Send bootstrap. The mechanism is therefore new experimental host glue, not a replacement for a selected production component.

## Architecture primitives / engineering domains

1. **Explicit opt-in deep-link marker** — browser extension / capability-scoping domain.
   - Required guarantee: normal ChatGPT visits never auto-submit.
   - Failure boundary: stale/replayed launch links.
   - Mitigation: `cap_autosend=1` plus a run id duplicated inside the visible prompt.

2. **DOM readiness observation** — web platform DOM-observation domain.
   - Required guarantee: act only after composer/plugin/send controls exist.
   - Mechanism: `MutationObserver`, the standard DOM-change observation API.
   - Failure boundary: ChatGPT DOM/selector drift.
   - Mitigation: conservative selector + timeout + fail closed.

3. **At-most-one local physical submit attempt** — browser automation/idempotency domain.
   - Required guarantee: SPA rerenders must not cause duplicate clicks.
   - Mechanism: per-tab `sessionStorage` run-id state written before click.
   - Failure boundary: a click can be accepted while navigation/state feedback is delayed.
   - Mitigation: never auto-retry the same run id; later recovery must use a fresh run id after observing state.

## Problem evidence vs solution evidence

### Problem evidence

The manual probe directly demonstrated that the deep link already creates the desired ordinary Chat surface and plugin chip but leaves Send pending. Therefore a one-action bootstrap gap exists.

### Solution evidence

- Chrome Manifest V3 static content scripts are a supported mechanism for automatically running code on a narrowly matched site and can inspect/modify page DOM.
- Chrome documents that content scripts run in an isolated world by default and require explicit URL match patterns.
- `MutationObserver` is the standard, broadly available web API for observing DOM changes without polling the whole browser.
- No background service worker, `tabs`, `scripting`, network interception, broad host permission, native messaging, or external API is required for this experiment.

Primary references:

- Chrome Extensions `content_scripts`: https://developer.chrome.com/docs/extensions/reference/manifest/content-scripts
- Chrome Extensions content-script concepts: https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts
- MDN `MutationObserver`: https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver

## Materially distinct approaches

### A. Narrow Manifest V3 content script — selected for experiment

`Windows Task Scheduler -> open opt-in ChatGPT deep link -> content script validates composer/plugin/run id -> one Send click -> ordinary Chat worker`

Advantages:

- no paid API and no Work/Computer Use;
- no external automation runtime;
- no focus/keyboard dependency;
- can bind action to exact ChatGPT origin, query contract, visible plugin, and prompt run id;
- small permission surface.

Failures:

- private ChatGPT DOM can change;
- plugin chip render may lag or change structure;
- programmatic click is not equivalent to a human trusted input event in every web application.

Mitigation: experimental status + physical gate + fail closed; no selector guessing beyond reviewed bounded candidates.

### B. AutoHotkey / synthetic Enter

Advantages: tiny implementation and independent of DOM selectors when focus is correct.

Failures: global focus race, wrong-window/wrong-control send, keyboard-layout/focus ambiguity, harder to bind to plugin/prompt identity.

Decision: reject for first experiment because the consequence boundary is less observable and less fail-closed.

### C. Playwright/browser automation bootstrap

Advantages: strong DOM automation and explicit waits.

Failures: larger runtime/profile/session ownership, browser-launch coordination, more moving parts, potential conflict with user browser/session, and duplicates infrastructure for one click.

Decision: defer as fallback if the minimal extension cannot reliably submit.

## Failure matrix

| Situation | Required result |
|---|---|
| Normal `chatgpt.com` visit without opt-in query | no action |
| `cap_autosend=1` but no valid run id | no action |
| Query run id does not appear in visible composer sentinel | no action |
| Expected plugin chip absent | wait until timeout, then no action |
| Send button absent/disabled | wait until timeout, then no action |
| ChatGPT DOM selector changes | no action |
| SPA rerender after readiness | at most one attempt for the run id |
| Same run id URL reprocessed in same tab session | no second attempt |
| Click dispatched but effect is ambiguous | no automatic retry |
| Page navigates to conversation after click | extension becomes inert because opt-in query is gone / run id already attempted |

## Experimental acceptance

Before any scheduler integration or production status:

1. load unpacked extension in the user's Chrome;
2. open an opt-in deep link containing a fresh run id and `@Chat Local Bridge Test`;
3. independently observe the ordinary **Chat** surface, expected plugin chip, and automatic single Send;
4. resulting fresh chat must actually expose `Chat Local Bridge Test` and reach `workspace_read` once;
5. reopen/re-render/revisit with the same run id in the same tab and prove no duplicate Send;
6. open ordinary ChatGPT URLs without the opt-in contract and prove zero extension action;
7. if any selector mismatch or ambiguous state occurs, classify the run as fail/unknown rather than adding blind fallbacks.

Scheduler wake/resume, run-id generation, cross-restart deduplication, WorkingState ownership, and automatic worker rotation are explicitly out of scope until this physical bootstrap is proven.

## Decision

**NARROW**

Implement only a minimal unpacked Chrome Manifest V3 experimental extension that performs one fail-closed Send attempt for an explicitly run-id-bound ChatGPT deep link after verifying the expected plugin chip and run id in the same composer. Do not wire it into Windows Task Scheduler, WorkingState, production runtime, or any consequence-bearing path in this slice.
