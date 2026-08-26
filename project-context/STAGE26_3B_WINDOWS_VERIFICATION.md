# Stage 26.3B — Windows DesktopState Shared-Kernel Verification

Status: **ACTIVE PR #114 — physical target qualification required before merge**.

## Purpose

Connect the already accepted Windows `DesktopState` evidence to the same Stage 26.3B Verification Kernel used by file/artifact and Browser paths.

This slice does **not** add Windows action authority and does not add a Chat/MCP tool. It verifies the identity and final state of one already-bound live Windows application/window.

## Accepted foundation reused

The adapter consumes `DesktopState.to_mapping()` from `runtime/windows/observation.py`, which already records:

```text
Windows session
application identity = SHA-256 of normalized executable path
executable basename
PID
process generation = process creation time
HWND
window_instance digest
window title / bounds
focused UIA control evidence
bounded UIA controls
optional screenshot digest
frame digest
freshness evidence
```

The live observer remains the authority for collecting Win32/UIA evidence. The new Control Plane adapter is data-only and cannot enumerate windows, invoke UIA, deliver input, launch a process, or authorize an action.

## Shared-kernel path

```text
accepted DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> ObservationRef(sequence N)
 -> caller-declared bounded final-state expectation
 -> automatic stable process/native-window continuity predicates
 -> accepted DesktopState AFTER
 -> ObservationRef(sequence N+1)
 -> shared verify_expected_effect
 -> PASS | FAIL | UNKNOWN
```

`capability = windows.desktop`.

The logical observation subject is supplied by the caller. Stable process/window identity remains inside verifier state rather than being hidden in the subject, so process/native-window drift becomes an observable FAIL.

## Mandatory stable identity continuity

Every verified transition automatically requires equality of:

```text
session_id
application_identity
executable_name
process_id
process_generation
window_handle
coordinate_space
```

This means a process restart with PID reuse, process-generation drift, HWND change, executable/application identity drift or Windows-session drift cannot satisfy an otherwise similar final state.

These predicates are mandatory and cannot be disabled by the planner/caller.

### Why `window_instance` is not a continuity predicate

The accepted Stage 26.2 `DesktopState` defines `window_instance` as a digest of:

```text
process_id
process_generation
window_handle
window_title
```

Therefore a legitimate title change on the **same** PID/process-generation/HWND changes `window_instance`. Treating it as immutable identity would incorrectly reject valid title-changing transitions.

PR #114 instead **recomputes and validates** `window_instance` independently for every snapshot. It is snapshot-consistency evidence, not a separate stable window-generation token.

The same applies to control observation fingerprints and `frame_digest`: the adapter recomputes them from normalized DesktopState content and rejects contradictions before verification.

Current evidence cannot distinguish a destroy/recreate event that somehow reuses the same PID/process-generation/HWND and recreates an indistinguishable title/state. PR #114 does not claim such a stronger window-generation proof. A future capability that needs that distinction must collect a stronger native generation signal rather than overloading `window_instance`.

## Bounded caller postconditions

PR #114 intentionally starts small. The caller may verify only reviewed final-state evidence:

```text
window.title
window.focused_control
window.bounds

evidence.frame_digest
evidence.screenshot_digest
evidence.visible_text_sha256
```

Raw visible text is reduced to SHA-256 in verifier state. Screenshot bytes remain outside the state; only the accepted digest is carried through.

No arbitrary selector/expression, Python, PowerShell, shell, process command, Win32 call, UIA query, code execution, backend selector or generic dispatch is accepted as an expected state.

## Integrity, completeness and ambiguity

The accepted exact-window observer already fails closed on non-unique bound windows, oversized UIA scans and conflicting/ambiguous focus evidence.

The shared adapter additionally:

- recomputes each control `observation_fingerprint`;
- recomputes `window_instance` from process/HWND/title evidence;
- recomputes `frame_digest` from normalized DesktopState content;
- validates redundant `freshness_evidence` against top-level evidence;
- detects duplicate control observation fingerprints.

Digest/freshness contradictions are rejected as invalid evidence. Duplicate control fingerprints make the snapshot ambiguous; the common Verification Kernel returns `UNKNOWN`, not PASS, when unambiguous evidence is required.

## Relationship to the legacy Windows verifier

`runtime/windows/verifier.py` is preserved unchanged. It belongs to the accepted Stage 26.2 foundation and is still used by historical/regression evidence.

PR #114 adds the Stage 26.3B adapter in `runtime/control_plane` rather than silently changing the semantics of the older API.

## Physical target qualification

The qualification reuses the accepted harmless WinForms fixture and exact PID/HWND `observe_bound_window` path.

Required final-head evidence:

```text
two fresh live observations keep exact stable Windows identity
same-identity declared final state -> shared-kernel PASS
wrong declared final state -> FAIL
canonical synthetic process-generation drift -> FAIL
canonical synthetic HWND drift -> FAIL
stale observation -> UNKNOWN
no desktop fallback/binding ambiguity
fixture cleanup succeeds
```

Synthetic negative probes are verifier tests, not claims that the OS physically changed identity during the run. They are rebuilt through the production `build_desktop_state` path so their snapshot-local digests remain internally valid. Positive identity evidence comes from two fresh observations of the actual target-Windows fixture.

Harness:

```text
scripts/stage26-windows-verification-qualification.ps1
scripts/stage26-windows-verification-qualification.py
```

## Non-goals

This PR does not yet prove a natural-language Windows L3 task. It also does not implement process launch/exit verification, generic desktop action routing, or a public `desktop_*` tool.

After this verifier is physically accepted and merged, the next acceptance slice must compose accepted Windows action/observation mechanisms into one representative Windows/application L3 task with an independent Finish Gate.
