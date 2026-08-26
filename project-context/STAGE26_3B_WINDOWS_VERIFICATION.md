# Stage 26.3B — Windows DesktopState Shared-Kernel Verification

Status: **ACTIVE PR #114 — physical target qualification required before merge**.

## Purpose

Connect the already accepted Windows `DesktopState` evidence to the same Stage 26.3B Verification Kernel used by file/artifact and Browser paths.

This slice does **not** add Windows action authority and does not add a Chat/MCP tool. It verifies the identity and final state of one already-bound live Windows application/window.

## Accepted foundation reused

The adapter consumes `DesktopState.to_mapping()` from `runtime/windows/observation.py`, which already binds:

```text
Windows session
application identity = SHA-256 of normalized executable path
executable basename
PID
process generation = process creation time
HWND
window instance
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
 -> automatic exact identity-continuity predicates
 -> accepted DesktopState AFTER
 -> ObservationRef(sequence N+1)
 -> shared verify_expected_effect
 -> PASS | FAIL | UNKNOWN
```

`capability = windows.desktop`.

The logical observation subject is supplied by the caller. The process/window identity is deliberately kept inside verifier state rather than hidden in the subject, so process/window replacement becomes an observable FAIL instead of accidentally becoming a new accepted subject.

## Mandatory identity continuity

Every verified transition automatically requires equality of:

```text
session_id
application_identity
executable_name
process_id
process_generation
window_handle
window_instance
coordinate_space
```

Therefore a similar-looking window cannot satisfy a postcondition after:

- process restart with PID reuse;
- process-generation change;
- HWND reuse/change;
- window-instance replacement;
- executable/application identity drift;
- Windows-session drift.

These identity predicates are mandatory and cannot be disabled by the planner/caller.

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

## Completeness and ambiguity

The accepted exact-window observer already fails closed on non-unique bound windows, oversized UIA scans and conflicting/ambiguous focus evidence.

The shared adapter additionally detects duplicate `observation_fingerprint` values. Such a snapshot is marked ambiguous; the common Verification Kernel returns `UNKNOWN`, not PASS, when unambiguous evidence is required.

DesktopState freshness redundancy is checked during normalization. Contradictions between top-level process/window identity and `freshness_evidence` are rejected as invalid evidence rather than normalized away.

## Relationship to the legacy Windows verifier

`runtime/windows/verifier.py` is preserved unchanged. It belongs to the accepted Stage 26.2 foundation and is still used by historical/regression evidence.

PR #114 adds the Stage 26.3B adapter in `runtime/control_plane` rather than silently changing the semantics of the older API.

## Physical target qualification

The qualification reuses the accepted harmless WinForms fixture and exact PID/HWND `observe_bound_window` path.

Required final-head evidence:

```text
same two live observations keep exact Windows identity
same-identity declared final state -> shared-kernel PASS
wrong declared final state -> FAIL
synthetic process-generation drift -> FAIL
synthetic HWND/window-instance drift -> FAIL
stale observation -> UNKNOWN
no desktop fallback/binding ambiguity
fixture cleanup succeeds
```

Synthetic negative probes are verifier tests, not claims that the OS physically changed identity during the run. The positive identity evidence comes from two fresh observations of the actual target-Windows fixture.

Harness:

```text
scripts/stage26-windows-verification-qualification.ps1
scripts/stage26-windows-verification-qualification.py
```

## Non-goals

This PR does not yet prove a natural-language Windows L3 task. It also does not implement process launch/exit verification, generic desktop action routing, or a public `desktop_*` tool.

After this verifier is physically accepted and merged, the next acceptance slice must compose accepted Windows action/observation mechanisms into one representative Windows/application L3 task with an independent Finish Gate.
