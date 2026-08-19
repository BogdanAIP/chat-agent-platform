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

## Native search strategy

For a locator that includes `window_name`:

1. obtain the UIA root;
2. use native UIA property conditions to find exact top-level `WindowControl` matches with that Name, searching only `TreeScope.Children` of Desktop;
3. build native property conditions for the target:
   - `AutomationId` when supplied;
   - exact control type for role;
   - exact Name when supplied;
4. call native `FindAll(TreeScope.Descendants, condition)` on the matching window only;
5. pass each result through the pinned upstream candidate/fingerprint function;
6. preserve exact ambiguity handling;
7. on `/uia/act`, perform the same fresh window-scoped lookup again and let pinned upstream compare the expected fingerprint before action.

The project-owned resolver contains no manual `GetChildren()` DFS.

If a locator has no `window_name`, the qualification-only resolver can fall back to pinned upstream behavior, but the Stage 26.1E physical benchmark requires:

`DESKTOP_FALLBACK_CALLS=0`

All eight structural resolution calls per benchmark cycle must take the window-scoped path.

## AutomationId path

When a locator carries `AutomationId`, Stage 26.1E adds a native `AutomationIdProperty` condition. When it does not, exact role/control-type + Name conditions are used inside the already-scoped target window.

The current Stage 26 fixture primarily tests the role+name path. The benchmark records both `AUTOMATION_ID_CONDITION_CALLS` and `ROLE_NAME_CONDITION_CALLS` so later application fixtures can prove the stronger AutomationId path separately.

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

The persistent Stage 26.1D environment is reused. Stage 26.1E deliberately does not reinstall Python dependencies, so the next physical output directly answers whether UIA resolution itself became fast.

## Acceptance evidence

Correctness/safety gates remain hard:

- exact pinned environment;
- agent process reused;
- fixture process reused;
- expected operation sequence on every measured cycle;
- expected `8 * total_cycles` window-scoped structural resolution calls;
- `DESKTOP_FALLBACK_CALLS=0`;
- `UNRELATED_WINDOW_ACTION_COUNT=0`;
- `FALSE_ACTION_COUNT=0`;
- Chrome survival;
- fixture-owned cleanup only.

Performance is compared directly with the Stage 26.1D physical baseline:

- baseline action p50: `183606.855 ms`;
- baseline action p95: `185567.403 ms`;
- minimum Stage 26.1E improvement gate: `10x` on both p50 and p95.

The `10x` gate is only the minimum evidence that this resolver change meaningfully removes the measured bottleneck. It is not the final production interactive-latency budget; after the optimized physical numbers exist, the project can set a stricter UX target and decide whether any additional caching is warranted.

No production Chat semantic surface changes in this stage.
