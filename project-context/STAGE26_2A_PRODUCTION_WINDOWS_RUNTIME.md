# Stage 26.2A — Production Windows Runtime Foundation

## Status

**ACTIVE / DRAFT PR.**

This stage promotes already qualified Windows primitives out of `scripts/stage26-*`
research/qualification ownership and into maintained production runtime code.
It does **not** expose Windows control to ordinary ChatGPT yet.

## Base evidence

This stage is stacked on the accepted Stage 26.1E + documentation-sync line.
The production extraction must preserve the exact safety/performance properties
proved on the target machine:

```text
Stage 26.1C accepted executor head:
4bf08dd9b8d1ff010f14723f9bb0384b97334a2b

Stage 26.1D physical baseline:
p50 = 183606.855 ms
p95 = 185567.403 ms

Stage 26.1E accepted head:
66390aca1dadf57c4f11568ec311ad6fcdbd7596

Stage 26.1E physical optimized result:
p50 = 3323.570 ms
p95 = 3720.061 ms
p50 speedup = 55.244x
p95 speedup = 49.883x
WINDOW_SCOPED_FIND_CALLS = 97
WINDOW_NAME_MATCH_COUNT = 97
DESKTOP_FALLBACK_CALLS = 0
WINDOW_BINDING_FAILURES = 0
WINDOW_BINDING_AMBIGUITIES = 0
FALSE_ACTION_COUNT = 0
UNRELATED_WINDOW_ACTION_COUNT = 0
```

## Production modules introduced

```text
runtime/windows/
├─ __init__.py
├─ actuation.py
├─ verifier.py
└─ window_scoped_uia.py
```

### `window_scoped_uia.py`

Promotes the accepted resolver boundary:

```text
expected PID
  -> bounded Win32 EnumWindows
  -> exact process HWNDs
  -> UIA conversion only for same-process HWNDs
  -> exact normalized WindowControl name
  -> native FindAll inside that window only
  -> upstream candidate/fingerprint rules
  -> independent act re-resolution
```

Production invariants:

- no Desktop `GetRootControl()` traversal in the optimized path;
- no manual `GetChildren()` DFS;
- maximum top-level HWND enumeration bound;
- maximum per-window control scan bound;
- no HWND/control cache;
- no generic execution path;
- window binding happens before native condition-client construction;
- pinned `uiautomation` internal `_AutomationClient` is imported explicitly;
- the narrow upstream `_find_candidates` replacement is serialized so
  concurrent resolver calls cannot overlap module-global replacement state.

### `actuation.py`

Promotes the physically accepted bounded Unicode text path:

- exact UTF-16LE code units;
- Win32 `SendInput` + `KEYEVENTF_UNICODE`;
- complete x64 `INPUT` union (`MOUSEINPUT`, `KEYBDINPUT`, `HARDWAREINPUT`);
- bounded text length;
- bounded numeric interval;
- no clipboard;
- no keyboard-layout mutation;
- no shell/process execution;
- all non-`type_text` typed actions stay delegated to pinned OpenAdapt typed input.

### `verifier.py`

Introduces the Stage 26.2A verifier contract early enough for real application
E2E:

```text
action delivered != task completed
```

Verifier outcomes are exactly:

```text
PASS
FAIL
UNKNOWN
```

The verifier is explicitly non-authorizing.  Missing evidence is `UNKNOWN`,
contradictory current evidence is `FAIL`, and exact explicit current-state
postconditions are `PASS`.

This is only the foundation.  Application/file/window/procedure-specific
verifiers are added later without changing this authority boundary.

## Qualification reuse rule

The Stage 26.1E physical benchmark now loads:

```text
runtime/windows/window_scoped_uia.py
runtime/windows/actuation.py
```

directly.  It no longer measures only a qualification-owned resolver/input
copy.  Therefore the next physical rerun is evidence about the promoted
production primitives themselves.

Historical qualification scripts remain as evidence/reference until a later
cleanup; they are not the production source of truth for these promoted
mechanisms.

## CI gate

Hosted CI must prove:

- all production Python files parse;
- existing resolver architectural regressions target `runtime/windows`;
- benchmark points to the production resolver and actuation paths;
- PID/HWND scoping remains bounded/fail-closed;
- no Desktop full-tree walk is reintroduced;
- bounded Unicode input retains the accepted ABI/schema restrictions;
- verifier returns `UNKNOWN` for absent evidence, `FAIL` for contradiction and
  `PASS` only for explicit matching postconditions;
- no public Chat tool names are added;
- no generic exec/shell surface appears.

CI alone cannot accept native Windows runtime behavior.

## Required real Windows target gate

After exact-head CI is green, rerun the existing 2 warmup + 10 measured-cycle
physical benchmark on the target machine without touching the mouse/keyboard.

Required production-source evidence:

```text
PRODUCTION_RESOLVER_PATH=...runtime\windows\window_scoped_uia.py
PRODUCTION_ACTUATION_PATH=...runtime\windows\actuation.py
WINDOW_BINDING_PASS=True
PREFLIGHT_CANDIDATE_COUNT=1
PREFLIGHT_FINGERPRINT_PRESENT=True
WINDOW_SCOPED_FIND_CALLS=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
LAST_FAILURE_STAGE=<null>
LAST_FAILURE_DETAIL=<null>
AGENT_PROCESS_REUSED=True
FIXTURE_PROCESS_REUSED=True
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0
MINIMUM_SPEEDUP_PASS=True
ERROR=<null>
PASS=True
BENCHMARK_EXIT_CODE=0
```

Performance must remain above the existing 10x acceptance floor against the
Stage 26.1D physical baseline.  Stage 26.1E's ~3.3/3.7 s p50/p95 is the expected
reference, not a silently relaxed target.

## Explicit non-goals

This PR does not:

- merge the stacked prerequisite PRs;
- add `desktop_observe` / `desktop_interact` or any public MCP tool;
- integrate Windows into `semantic-projection`;
- implement `DesktopState` (Stage 26.2B);
- implement desktop VLM grounding (Stage 26.2C);
- implement semantic/UIA -> vision routing (Stage 26.2D);
- claim real-application accuracy (Stage 26.2E);
- integrate procedural memory;
- add a local planner/reasoner;
- change the ChatGPT-only planner boundary.

## Acceptance decision

Only after deterministic CI **and** the exact-head real Windows production-source
benchmark pass may Stage 26.2A be marked accepted/ready for landing after its
prerequisite stack.
