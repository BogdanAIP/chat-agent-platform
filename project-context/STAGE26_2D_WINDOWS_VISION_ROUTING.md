# Stage 26.2D — Windows UIA -> Vision Routing + Freshness Authorization

Status: **ACTIVE — hosted adversarial CI + physical target qualification required**

Base `main` at branch creation:

`a4a419616dc6f516b801b456a924b03a77dea22d`

## Goal

Integrate the accepted Windows observation, structural UIA, desktop Grounder and guarded executor into one deterministic structure-first routing boundary.

This stage is the first Windows path allowed to turn an accepted visual proposal into one real bounded click. The VLM never authorizes the action itself.

## Production seam

`runtime/windows/routing.py`

Primary operation:

```text
route_desktop_click(
  request,
  observe,
  ground,
  execute_structural,
  execute_coordinate
) -> DesktopRoutingResult
```

The router is intentionally dependency-injected so policy can be adversarially tested without real mutation. Production helper functions adapt the accepted OpenAdapt Windows backend for independently re-resolved UIA clicks and the Stage 26.1C guarded-coordinate click path.

The module is not re-exported from `runtime/windows/__init__.py`; ordinary Windows observation/execution imports therefore do not acquire an eager local-VLM/Pillow dependency.

## Routing policy

Normal order:

```text
fresh DesktopState
 -> exact native structure?
      -> exactly one visible+enabled target
      -> fresh same-window re-observation
      -> independently re-resolved native UIA action

 -> true structural miss?
      -> visual fallback must be explicitly promoted as `zero-exact-candidate`
      -> exact-window PNG + DesktopState
      -> Stage 26.2C Grounder proposal or ABSTAIN
      -> fresh exact-window re-observation after inference
      -> same session/application/process-generation/PID/HWND/window-instance/bounds
      -> same frame_digest + screenshot_digest
      -> proposal evidence still matches current state
      -> Stage 26.1C guarded-coordinate frame binding
      -> exactly one physical click OR ABSTAIN
```

## Cases that do not escalate to vision

The router fails closed before VLM when structure is not a true zero-exact miss:

- multiple exact structural candidates;
- exact target hidden, disabled or visibility/enabled unknown;
- exact text with conflicting role;
- supplied AutomationId not found;
- supplied AutomationId conflicts with role/name;
- visual fallback not explicitly promoted.

Semantic ambiguity is therefore not converted into a visual guess.

## Freshness / TOCTOU boundary

A proposal is not executable merely because the Grounder accepted it.

After model inference the router obtains a new exact-window observation and requires:

- same session identity;
- same application identity;
- same PID and process generation;
- same HWND and window instance;
- same window title/bounds/coordinate space;
- exact same `frame_digest`;
- exact same `screenshot_digest`;
- proposal identity/frame/coordinate evidence still matches the fresh state;
- no exact structural target has appeared in the meantime.

Any mismatch produces ABSTAIN and zero action.

The coordinate executor then applies the already accepted second freshness boundary:

```text
arm_guarded_coordinate
 -> backend fresh screenshot
 -> expected_frame_sha256
 -> act_guarded_coordinate
```

Thus exact-window authorization and actual click delivery have independent freshness checks.

## Delivery is not completion

The router accepts only delivery receipts with:

```text
status = delivered
outcome_verified = false
```

Structural route operations must be native `uia_*`. Visual route delivery must be exactly `physical_click`.

Task completion remains the verifier/postcondition layer; a delivery receipt cannot claim task success.

## Hosted adversarial suite

`tests/test_stage26_2d_windows_vision_routing.py` covers:

- structure wins without VLM;
- duplicate exact structure -> ABSTAIN;
- hidden/disabled/unknown target -> ABSTAIN;
- role conflict -> ABSTAIN;
- AutomationId miss -> ABSTAIN;
- zero exact candidate without explicit promotion -> ABSTAIN;
- Grounder ABSTAIN -> zero action;
- valid visual proposal -> exactly one coordinate executor call after fresh re-observation;
- changed screenshot/frame -> zero action;
- changed PID/process-generation/HWND/window -> zero action;
- proposal evidence mismatch/out-of-window point -> zero action;
- structure appearing after Grounder -> zero action;
- stale observation -> zero action;
- delivery receipt cannot claim completion;
- no shell/generic dispatcher/type/press/scroll channel is introduced.

## Physical target qualification

Harness:

`scripts/stage26-desktop-routing-qualification.ps1`

Driver:

`scripts/stage26-desktop-routing-qualification.py`

The controlled WinForms fixture is used because Stage 26.2C already proved the local LFM2.5-VL can visually resolve rendered `1. Benchmark start` while UIA exposes `Stage 26 start button`.

Physical run performs:

1. visual fallback disabled probe -> ABSTAIN, zero VLM/action;
2. exact-name role-conflict probe -> ABSTAIN, zero VLM/action;
3. one explicitly promoted visual fallback for `1. Benchmark start`;
4. fresh exact-window re-observation after model inference;
5. one guarded physical click only if evidence is unchanged;
6. fixture postcondition must show only `start_clicked=True` while text/enter/scroll/finish remain False.

Required physical gates:

```text
VISION_READY_PASS=True
VISION_RESTORED_PASS=True
AGENT_LOOPBACK_PASS=True
AGENT_AUTH_REQUIRED_PASS=True
LEGACY_CAPABILITY_ABSENT_PASS=True
VISION_DISABLED_ABSTAIN_PASS=True
ROLE_CONFLICT_ABSTAIN_PASS=True
NEGATIVE_ZERO_ACTION_PASS=True
POSITIVE_VISUAL_ROUTE_PASS=True
FRESH_REOBSERVATION_PASS=True
GUARDED_CLICK_RECEIPT_PASS=True
FIXTURE_START_POSTCONDITION_PASS=True
FIXTURE_NO_EXTRA_MUTATION_PASS=True
SINGLE_ACTION_PASS=True
STRUCTURAL_EXECUTOR_CALLS=0
COORDINATE_EXECUTOR_CALLS=1
GROUNDER_CALLS=1
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
FIXTURE_KILLED=False
FIXTURE_CLEANUP_PASS=True
DRIVER_ERROR=<null>
ERROR=<null>
STAGE26_2D_WINDOWS_VISION_ROUTING_RESULT=PASSED
```

## Non-goals

Stage 26.2D does not claim:

- universal Windows accuracy;
- cross-application visual success;
- arbitrary coordinate actions;
- text/keyboard/scroll visual routing;
- public `desktop_*` MCP tools;
- task completion from action delivery;
- procedural memory integration.

The physical gate is one controlled real visual click. The adversarial suite establishes the fail-closed routing policy; Stage 26.2E remains the first real medium-complexity application E2E.
