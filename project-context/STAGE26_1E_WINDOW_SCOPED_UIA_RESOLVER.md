# Stage 26.1E — window-scoped native UIA resolver

## Why this stage exists

Stage 26.1D physically measured the accepted Windows executor on the target host. Correctness passed, but warm interactive latency did not:

- action sequence p50: `183606.855 ms`;
- action sequence p95: `185567.403 ms`;
- Start UIA p50: `45382.333 ms`;
- Focus UIA p50: `45117.606 ms`;
- row UIA find p50: `22714.528 ms`;
- Finish UIA p50: `46097.307 ms`.

Guarded physical operations were much faster:

- click p50: `361.695 ms`;
- press p50: `374.779 ms`;
- scroll p50: `371.198 ms`;
- text p50: `601.466 ms`.

The exact pinned upstream explains the shape. `_find_candidates()` starts at `auto.GetRootControl()` and manually walks descendants via `GetChildren()`. `/uia/act` calls the same resolver again before comparing the expected fingerprint, so one structural `find + act` performs two desktop-wide walks.

## Optimization boundary

Stage 26.1E changes only candidate resolution for typed `/uia/find` and `/uia/act` inside the benchmark agent. It uses the existing upstream injection seam:

`create_server(..., uia_fn=...)`

Everything else remains pinned upstream or already accepted Stage 26.1C behavior:

- bearer authentication;
- loopback bind;
- legacy exec disabled;
- typed request schema;
- guarded screenshot freshness;
- execution context freshness;
- focused-target check for keyboard input;
- target candidate construction;
- target fingerprint construction;
- `/uia/act` re-resolution;
- expected fingerprint comparison;
- native UIA action patterns;
- layout-independent text input;
- physical guarded click/press/scroll.

## Physical failure history and corrected window binding

The first physical Stage 26.1E head used `Control.FindAll(...)`, but `uiautomation==2.0.29` exposes native `FindAll` on the wrapped COM `Element`, not on `Control`. That run failed before target conditions were evaluated.

The second physical head corrected the raw COM adapter to `control.Element.FindAll(...)`, but exact UIA `NameProperty` matching on Desktop `TreeScope.Children` still returned no top-level fixture window. The evidence was again fail-fast and non-actuating:

- `WINDOW_SCOPED_FIND_CALLS=1`;
- `AUTOMATION_ID_CONDITION_CALLS=0`;
- `ROLE_NAME_CONDITION_CALLS=0`;
- `UNRELATED_WINDOW_ACTION_COUNT=0`;
- `FALSE_ACTION_COUNT=0`.

Stage 26.1E therefore no longer uses Desktop UIA search to bind the target window.

For qualification the fixture publishes its exact PID before structural work begins. The resolver now:

1. enumerates only top-level HWNDs with Win32 `EnumWindows`;
2. filters those HWNDs by the exact expected process id with `GetWindowThreadProcessId`;
3. converts only same-process HWNDs to UIA controls with `uiautomation.ControlFromHandle`;
4. requires `WindowControl` and exact normalized UIA window Name;
5. only after the exact window is bound, performs native UIA `FindAll(TreeScope.Descendants, ...)` inside that window.

This removes desktop UIA traversal entirely from the optimized path and narrows observation before UIA conversion to the target process.

Window enumeration is bounded. An absent process context, enumeration truncation, no exact window match, or ambiguous binding fails closed before any action.

## Native target search strategy

Inside the bound window:

- if `AutomationId` is supplied, native UIA conditions use exact `AutomationIdProperty` plus the expected control type;
- when `AutomationId` is absent, native UIA narrows by exact control type only, then the pinned upstream candidate layer performs the exact normalized `Name`, role, window-name and fingerprint checks.

This provider-tolerant fallback is deliberate. The physical WinForms qualification proved that raw UIA `NameProperty` equality cannot be assumed to behave identically to the normalized `Control.Name` value used by the accepted upstream candidate model. The fallback therefore avoids another raw `NameProperty` dependency while still scanning only one already-bound target window. The per-window native result scan is bounded at 512 controls.

The project-owned resolver contains no manual `GetChildren()` DFS and no Desktop `GetRootControl()` search.

Native `IUIAutomationElementArray` values returned by `FindAll` are converted with the same shape used by `uiautomation`: `Length`, `GetElement(index)`, then `Control.CreateControlFromElement(...)`.

Each `/uia/act` still performs a fresh PID/HWND window binding and fresh target lookup. No HWND/control cache is introduced in this stage. The pinned upstream implementation still compares the expected target fingerprint immediately before action.

If a locator has no `window_name`, the qualification-only resolver can fall back to pinned upstream behavior, but physical Stage 26.1E requires:

`DESKTOP_FALLBACK_CALLS=0`

## Non-actuating preflight

Before cycle 1, the benchmark binds the exact fixture PID and performs one structural lookup of the Start button without actuating it.

Required preflight evidence:

- `WINDOW_BINDING_PASS=True`;
- `PREFLIGHT_CANDIDATE_COUNT=1`;
- `PREFLIGHT_FINGERPRINT_PRESENT=True`;
- zero window-binding failures;
- zero window-binding ambiguities.

If preflight fails, the benchmark stops before any cycle action. Diagnostic counters report:

- `WINDOW_ENUM_CALLS`;
- `WINDOW_ENUM_HANDLES_SEEN`;
- `PROCESS_WINDOW_HANDLES_SEEN`;
- `WINDOW_UIA_CONVERTIBLE_COUNT`;
- `WINDOW_NAME_MATCH_COUNT`;
- `WINDOW_BINDING_FAILURES`;
- `WINDOW_BINDING_AMBIGUITIES`.

## AutomationId path

The current Stage 26 fixture primarily tests the role+normalized-name fallback. Later fixtures with stable `AutomationId` values can prove the stronger direct AutomationId path separately. The benchmark records both `AUTOMATION_ID_CONDITION_CALLS` and `ROLE_NAME_CONDITION_CALLS`.

## Benchmark relationship

Stage 26.1E reuses the Stage 26.1D fixture and the exact same seven-operation cycle:

1. UIA Start;
2. UIA focus textbox;
3. guarded text;
4. guarded Enter;
5. UIA row resolution + guarded coordinate click;
6. guarded scroll;
7. UIA Finish.

Default run remains two warm-up cycles plus ten measured cycles in one persistent executor and one persistent fixture.

The persistent Stage 26.1D environment is reused. Stage 26.1E deliberately does not reinstall Python dependencies.

## Acceptance evidence

Correctness/safety gates remain hard:

- exact pinned environment;
- preflight window binding pass;
- exact fixture process scope;
- agent process reused;
- fixture process reused;
- expected operation sequence on every measured cycle;
- expected `(8 * total_cycles) + 1` optimized structural resolution calls, including preflight;
- `DESKTOP_FALLBACK_CALLS=0`;
- `WINDOW_BINDING_FAILURES=0`;
- `WINDOW_BINDING_AMBIGUITIES=0`;
- `UNRELATED_WINDOW_ACTION_COUNT=0`;
- `FALSE_ACTION_COUNT=0`;
- Chrome survival;
- fixture-owned cleanup only.

Performance is compared directly with the Stage 26.1D physical baseline:

- baseline action p50: `183606.855 ms`;
- baseline action p95: `185567.403 ms`;
- minimum Stage 26.1E improvement gate: `10x` on both p50 and p95.

The `10x` gate is only the minimum evidence that this resolver change meaningfully removes the measured bottleneck. It is not the final production interactive-latency budget.

No production Chat semantic surface changes in this stage.
