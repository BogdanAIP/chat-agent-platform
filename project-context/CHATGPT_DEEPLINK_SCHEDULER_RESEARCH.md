# ChatGPT deep-link one-shot scheduler bootstrap — Stage Research Brief

Date: 2026-08-29
Base: `main` at `61a8dfa6e5f4310760b1b605d706c09854ab6ebf`
Depends on: `CHATGPT_DEEPLINK_AUTOSEND_RESEARCH.md`
Scope: one-shot target-Windows launcher/scheduler probe only; no recurring autonomous runtime, WorkingState lease, worker rotation, or production scheduling authority.

## Stage question

After the physical autosend gate proved

```text
external ChatGPT deep link
 -> fresh ordinary Chat
 -> Chat Local Bridge Test attached
 -> extension sends exactly one prompt
 -> workspace_read reaches the bridge
```

can target Windows create the same fresh ordinary-Chat worker from a local scheduled task without paid API usage, ChatGPT Work, Computer Use, Codex automation, or a long-lived local daemon?

## New physical problem/solution evidence

The 2026-08-29 target-browser probe produced `DEEPLINK_AUTOSEND_BRIDGE=PASS`: the extension automatically submitted the run-id-bound prompt, the resulting ordinary Chat exposed `Chat Local Bridge Test`, and `workspace_read` reached the bridge exactly once. This closes the prerequisite that the prior research intentionally left unresolved before scheduler integration.

The remaining bootstrap gap is now only deterministic local URL construction plus one interactive browser launch at a selected time.

## Durable invariants

- ordinary ChatGPT remains the only general planner;
- the accepted six-tool semantic surface and Secure MCP Tunnel route are unchanged;
- the Windows launcher generates only correlation/run identity and a ChatGPT URL; it has no Bridge, shell-execution, model, Work, Codex, or task-completion authority;
- a scheduled probe must run only in the signed-in interactive user session because the desired effect is opening that user's ordinary browser/ChatGPT surface;
- one scheduled probe launches one fresh run id once; no blind recurring loop is introduced in this slice;
- failed browser launch, missing extension/plugin, logged-out ChatGPT, DOM drift, or Bridge failure remains visible downstream and must not trigger an automatic same-run retry;
- run id remains non-secret correlation/deduplication data, not a capability grant.

## Architecture lineage comparison

| Role | Prior boundary | Decision | Reason |
|---|---|---|---|
| General planning | ordinary ChatGPT | `KEEP` | Scheduler only wakes a fresh Chat turn. |
| Chat reachability | Secure MCP Tunnel + official tunnel-client | `KEEP` | URL launch does not replace MCP transport. |
| Agent session / wake lifecycle | Codex reference-only; wake semantics unresolved | `REFINE` experimental candidate only | Target-Windows Task Scheduler becomes a narrow external wake source, not an agent runtime. |
| Capability-spanning state | project WorkingState | `KEEP` | Not read or mutated by this one-shot launcher; later resume ownership remains project-owned. |
| Authorization / verification / Finish Gate | project-owned | `KEEP` | Starting a chat is neither task success nor consequence authorization. |

No existing accepted component owns target-Windows interactive wake of an ordinary ChatGPT browser surface.

## Architecture primitives and evidence

### 1. One-shot Windows scheduled process launch

Engineering domain: Windows Task Scheduler / OS process scheduling.

Microsoft documents `schtasks`/Task Scheduler as the built-in facility for creating scheduled tasks that run a specified executable or script, including one-time schedules. The task executes under a selected user/security context. For this experiment the required context is the currently signed-in user, not SYSTEM, because a browser window must appear in that user's interactive desktop.

Primary reference:
- Microsoft Learn, `schtasks create`: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create
- Microsoft Learn, `schtasks`: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks

### 2. Fresh run-id-bound URL construction

Engineering domain: correlation/idempotency identity.

A fresh GUID-derived run id is generated before each intended launch and appears both in query parameters and the visible prompt sentinel required by the already-tested extension. This does not prove task uniqueness across multiple independently scheduled invocations; it only prevents the extension from repeating the same run id in one tab session.

### 3. Interactive default-browser URI launch

Engineering domain: Windows shell URI association.

The launcher delegates the HTTPS URI to the user's registered browser rather than automating Chrome windows, keyboard focus, or DOM. Browser choice/extension installation is therefore an environmental prerequisite that the physical gate must observe.

## Materially distinct approaches

### A. Task Scheduler -> bounded PowerShell URL launcher — selected

Advantages: uses built-in Windows scheduling; no daemon; no browser focus automation; run id generated at execution time; very small failure surface.

Failure boundary: task may run without an interactive logged-in desktop, the default browser may not contain the extension, ChatGPT may be logged out, or multiple separately-created tasks may each create independent workers.

Mitigation in this slice: create only a one-shot interactive-user probe; no recurrence or self-rescheduling; downstream extension remains fail-closed.

### B. Extension background alarms/scheduling

Would require persistent/background extension responsibilities and additional permissions/lifecycle semantics. It also depends on the browser already running and would move wake authority into the extension.

Decision: reject for this slice as unnecessary expansion.

### C. Long-lived local watcher/daemon

Could own richer wake/retry state but adds process lifecycle, restart, install/update, locking and authority questions before the one-shot mechanism is proven.

Decision: defer.

### D. AutoHotkey/GUI scheduler automation

Could open/focus Chrome and type, but reintroduces wrong-window/focus ambiguity that the deep-link approach already eliminated.

Decision: reject.

## Failure matrix

| Situation | Required result |
|---|---|
| One-shot task fires with user logged in | launcher generates fresh run id and opens exactly one deep link |
| Task runs non-interactively / user logged out | no claim of successful Chat wake; no retry loop |
| Default browser lacks extension | prompt may remain unsent; no launcher fallback click |
| ChatGPT logged out | login page/environment failure; no same-run retry |
| Plugin fails to resolve | extension times out and sends nothing |
| Browser/extension DOM contract drifts | extension sends nothing |
| Bridge/tunnel unavailable after send | Chat reports downstream failure; launcher does not retry |
| Launcher is invoked twice independently | two distinct run ids/workers are possible; recurrence/lease control is explicitly out of scope |
| Same scheduled action process crashes after URI handoff | outcome is ambiguous; no automatic same-run retry |

## Acceptance for this slice

1. hosted tests prove deterministic URL construction for a supplied run id and fail closed on malformed prompt/template inputs;
2. hosted PowerShell parse/test coverage proves the one-shot task registration command/spec is bounded to the current interactive user and one trigger;
3. on target Windows, register one probe a few minutes ahead;
4. without user click/Computer Use/Work, observe a fresh ordinary Chat open and autosend;
5. resulting chat reports the expected run id and `DEEPLINK_AUTOSEND_BRIDGE=PASS` (or a truthful downstream Bridge error if intentionally testing reachability);
6. inspect Task Scheduler history/status to show the launcher itself ran once;
7. no recurring schedule, worker rotation, WorkingState resume, lease, or automatic retry is accepted by this gate.

## Decision

**NARROW**

Implement only a one-shot target-Windows PowerShell launcher plus a helper that can register one interactive-user scheduled probe. Generate a fresh run id at launcher execution, build the already-qualified opt-in deep link, and delegate the HTTPS URI to the user's browser. Do not add recurrence, daemon lifecycle, WorkingState ownership/resume, worker completion detection, automatic retries, or production scheduler authority in this slice.
