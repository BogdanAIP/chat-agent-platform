# Stage 26.1C — Windows executor security A/B qualification

Status: **DRAFT / FIRST REAL TARGET RUN CLASSIFIED AS TRANSPORT-HARNESS DEFECT / RERUN REQUIRED**

Branch base resolved from live `main` after accepted Stage 26.1B documentation:

`def67e45d7a72547c53bcf339d00124f4edca0be`

Stage 26.1B accepted pinned OpenAdapt Capture for bounded real Windows demonstration recording and explicit RDP conversion, while correctly refusing to claim native-Windows replay. Stage 26.1C now evaluates the missing actuation boundary before any Windows executor is allowed into the product path.

## Question

> Can the exact pinned OpenAdapt Windows backend/agent be constrained to a typed, authenticated, interactive-session-only executor with stale-state and UIA uniqueness guards, while making its legacy arbitrary-Python route unreachable from the project-controlled launch path?

If yes, reuse the mature upstream actuation mechanisms behind a narrower project-owned launch/client boundary. If no, the measured blocker justifies a project-owned native actuator.

## Product boundary

This PR is **qualification only**.

It does not:

- add a Windows tool to the public Chat surface;
- integrate OpenAdapt into production `semantic-projection`;
- start a Windows executor from ordinary ChatGPT;
- run stored procedures against real user applications;
- expose a generic command, shell, Python, PowerShell or `tool_invoke` path;
- change the accepted five public semantic tool names;
- claim that delivery receipts prove workflow outcomes.

Ordinary ChatGPT remains the only planner/intelligence.

## Exact upstream

Inherited from `config/stage26-openadapt-lock.json`:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7
Python 3.12.x
```

The target harness installs the exact VCS commit into an isolated venv and verifies installed `direct_url.json` plus declared version before the fixture is allowed to receive any action.

## First real target run — transport-harness defect, no executor action

First real Windows target run used qualification HEAD:

`13bf8b51f04d2df3a7a70b45f9dc911f4d43b69a`

Evidence directory:

```text
C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\executor-qualification\executor-20260818-211345\
```

Observed before the failure:

```text
FLOW_PIN_PASS=True
AGENT_LOOPBACK_PASS=True
AGENT_AUTH_REQUIRED_PASS=True
LEGACY_CAPABILITY_ABSENT_PASS=True
DELIVERED_OPERATIONS=[]
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0
CHROME_PROCESS_COUNT_BEFORE=11
CHROME_PROCESS_COUNT_AFTER=11
CHROME_SURVIVAL_PASS=True
FIXTURE_KILLED=False
FIXTURE_CLEANUP_PASS=True
```

The driver then failed on the first negative POST with:

```text
ConnectionError: ConnectionAbortedError(10053, ... host computer aborted the established connection ...)
```

This is classified as a qualification transport defect, not an executor/UIA failure and not an operator error.

Pinned `win_agent.server` checks route availability and bearer authorization **before** reading `Content-Length` and the request body. The original qualification driver sent a JSON body for the deliberately unauthenticated `/input` probe. On this Windows target that pre-body rejection surfaced as a local TCP abort/reset (`WinError 10053`) before `requests` received the intended HTTP `401`. The disabled `/execute_windows` route has the same pre-body routing shape for `404`.

Correction:

- the `unauthorized POST /input -> 401` probe now uses an explicit zero-length POST body;
- the authorized disabled-route `POST /execute_windows -> 404` probe also uses an explicit zero-length body;
- both still prove the same live routing/auth properties;
- authorized typed-schema probes continue to send real JSON bodies and therefore still exercise the pinned parser;
- regression tests lock the zero-body transport contract;
- no acceptance gate is weakened and no legacy route is enabled.

The first run is **not** retroactively accepted. The corrected qualification must pass deterministic CI at its new exact HEAD and then pass a new exact-head Windows target rerun.

## A/B result before target acceptance

### A — OpenAdapt typed WindowsBackend + hardened typed win_agent

Pinned upstream already implements:

- loopback-default Windows agent;
- optional bearer authentication;
- typed `/input` operations with an exact bounded schema;
- `/input/guarded` with fresh-frame, execution-context and keyboard-focus checks;
- UIA locator/find with explicit unique/ambiguous outcomes;
- target fingerprints binding locator, geometry and native UI identity;
- `/uia/act` with fingerprint-bound native UIA patterns;
- delivery receipts that explicitly leave `outcome_verified=false`;
- a legacy `/execute_windows` compatibility route that is disabled when `AgentConfig.allow_legacy_exec=False`.

The project candidate does **not** invoke upstream CLI `main()` and exposes no argument passthrough. It constructs directly:

```python
AgentConfig(
    host="127.0.0.1",
    port=0,
    token=<random per-run secret>,
    allow_legacy_exec=False,
)
```

and the paired client is constructed with:

```python
WindowsBackend(
    server_url=<ephemeral loopback URL>,
    auth_token=<same secret>,
    require_tls=False,   # loopback-only qualification
    allow_legacy_exec=False,
)
```

This removes the `--allow-legacy-exec` CLI switch from the project-controlled startup surface while retaining exact upstream typed behavior.

### B — project-owned native actuator replacement

A replacement could remove the dormant legacy handler source and potentially avoid a local HTTP listener entirely. However, it would also duplicate substantial pinned upstream mechanisms already present and tested upstream:

- typed request validation;
- interactive-session observation;
- guarded freshness/context/focus binding;
- UIA candidate enumeration and ambiguity refusal;
- native target fingerprinting;
- native Invoke/Toggle/Select/Focus patterns;
- action-delivery uncertainty semantics.

Repository policy says not to duplicate mature upstream mechanisms without a measured integration/security/product blocker. Therefore B is **not implemented pre-emptively**. The real target qualification is designed to expose such a blocker if one exists.

### Candidate decision

Before the real target run:

```text
A = preferred candidate: ADOPT typed upstream executor mechanics
    + ADAPT with project-controlled no-passthrough launch boundary

B = reserve fallback: implement only if the target/security gate exposes
    a blocker that cannot be closed without weakening project invariants
```

This is not final production approval.

## Legacy-exec reachability contract

The project-controlled candidate must prove all of these on the live process:

```text
AgentConfig.allow_legacy_exec = false
WindowsBackend.allow_legacy_exec = false
health.capabilities does not contain legacy_exec
authorized zero-body POST /execute_windows -> 404
unauthorized zero-body POST /input -> 401
command-shaped extra field on authorized /input -> 400
unsupported authorized action=exec -> 400
```

The zero-body form is deliberate for the two responses produced before the pinned server reads a request body; it avoids the observed Windows pre-body TCP abort while preserving the routing/auth property under test.

A source-level dormant handler inside the exact upstream dependency is not treated as harmless by assertion alone. The live target process must prove the route is absent from routing while running under the exact construction path proposed for the product.

The target driver itself contains no `exec()`, `eval()`, subprocess shell or generic command execution mechanism.

## Interactive-session contract

A desktop executor that runs in Windows session 0 would be functionally and security-wise incorrect: it could observe or actuate a different desktop from the logged-on user.

Target acceptance therefore requires:

- `/health.active_console_session > 0`;
- `WindowsBackend.session_identity()` returns a valid native session digest;
- the latter can only be produced by pinned upstream when the process is attached to the active console session.

No service/session-0 deployment is accepted by this gate.

## Freshness and context refusal

Before enabling the fixture, the driver sends two deliberately non-mutating probes. Their payload is a zero-notch scroll, so even a guard regression emits no pointer/keyboard edge.

Required refusals:

```text
wrong expected frame SHA-256 -> HTTP 409 stale_frame
fresh frame + wrong application identity -> HTTP 409 stale_context
```

For real keyboard actions, the backend additionally binds the live UIA focus to the exact textbox point and requires a fresh screenshot digest before delivery.

## UIA uniqueness and fingerprint binding

The harmless WinForms fixture from Stage 26.1B is reused. Its UIA top-level accessibility name is:

`Stage 26 capture qualification fixture`

Targets are never selected by coordinate alone initially. The driver uses exact role+name+window UIA locators and requires one unique candidate plus a native fingerprint.

Qualification targets:

```text
button   Stage 26 start button
textbox  Stage 26 capture input
listitem Qualification row 01
button   Stage 26 finish button
```

Native UIA action uses the exact fingerprint returned by the unique resolution. A changed/reopened/replaced candidate must therefore be refused as stale.

## Harmless real action sequence

Unlike Stage 26.1B, the operator does **not** perform the sequence. This stage is qualifying the executor itself.

After every non-mutating security preflight passes, the fixture is enabled and the pinned backend performs only:

1. unique UIA resolution + fingerprint-bound native Invoke on Start;
2. unique UIA resolution + native Focus on the textbox;
3. guarded typed text `CAPTURE_OK` with fresh frame/context/focus;
4. guarded physical `Enter` with fresh frame/context/focus;
5. unique UIA resolution of `Qualification row 01` and guarded coordinate click inside it;
6. guarded three-notch downward scroll while the pointer is bound to that fixture list item;
7. unique UIA resolution + fingerprint-bound native Invoke on Finish.

The fixture independently proves the expected sequence and exact text.

No work application, user file, browser tab or real user workflow is targeted.

## Operator rule for the real target run

When the qualification fixture appears:

**do not click, type, move the mouse, scroll or switch windows until the fixture reaches DONE.**

External input is expected to trigger freshness/focus refusal and should be treated as a failed qualification run, not bypassed.

## Required target gates

```text
FLOW_PIN_PASS=True
DRIVER_PASS=True
AGENT_LOOPBACK_PASS=True
AGENT_AUTH_REQUIRED_PASS=True
LEGACY_CAPABILITY_ABSENT_PASS=True
LEGACY_ROUTE_404_PASS=True
UNAUTHORIZED_INPUT_401_PASS=True
COMMAND_FIELD_REJECTED_PASS=True
UNSUPPORTED_ACTION_REJECTED_PASS=True
INTERACTIVE_SESSION_PASS=True
STALE_FRAME_REFUSAL_PASS=True
STALE_CONTEXT_REFUSAL_PASS=True
UIA_UNIQUE_TARGET_PASS=True
FINGERPRINT_BOUND_ACTION_PASS=True
GUARDED_KEYBOARD_PASS=True
GUARDED_COORDINATE_PASS=True
GUARDED_SCROLL_PASS=True
FIXTURE_SEQUENCE_PASS=True
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0
LEGACY_EXEC_ENABLED=False
WINDOWS_BACKEND_ALLOW_LEGACY_EXEC=False
CHROME_SURVIVAL_PASS=True
FIXTURE_KILLED=False
FIXTURE_CLEANUP_PASS=True
STAGE26_1C_EXECUTOR_RESULT=PASSED
```

Any failed gate remains evidence. Do not enable the legacy route, loosen UIA uniqueness, remove freshness checks, widen the target to a real application, or add a generic executor to make the test pass.

## Local evidence and privacy

The target harness persists only bounded JSON state/result evidence under:

```text
%LOCALAPPDATA%\ChatAgentPlatform\stage26\executor-qualification\executor-<timestamp>\
```

Screenshots used by the guarded backend are held in memory and are not written by the Stage 26.1C driver. The random bearer token is also memory-only and is not stored in result JSON.

The isolated venv is removed by default after the run. Chrome is counted before/after but never closed or killed. Emergency termination is restricted to the exact qualification-owned fixture process.

## Decision after target pass

If all target gates pass, Stage 26.1C executor A/B can accept:

```text
OpenAdapt WindowsBackend + typed win_agent mechanics: ADOPT
project startup/client restriction: ADAPT
legacy compatibility route in product configuration: FORBIDDEN / PROVEN UNREACHABLE
full project-owned actuator replacement: DO NOT BUILD absent a new measured blocker
```

This still does not expose Windows actuation to Chat or declare the desktop product surface complete. Product integration belongs to later Stage 26 steps.

## F16 seam after executor acceptance

Only after the executor gate is accepted, prototype the already accepted local `LFM2.5-VL-450M F16` through OpenAdapt's narrow `Grounder` protocol:

```python
locate(screen_png, intent, ocr_text=None) -> GrounderMatch | None
```

The existing Stage 25 production visual CLI is browser/CSS-viewport specific. Stage 26.1C must not falsify native/window screenshot coordinates as `css_viewport`; the desktop Grounder adapter needs its own truthful pixel-space contract while reusing the reviewed local llama.cpp/model profile.

Grounder output is proposal-only. UIA/identity/freshness/risk/effect verification remains authoritative, and a model proposal never becomes authorization by itself.