# Stage 26.3B — Windows DesktopState Shared-Kernel Verification

Status: **ACTIVE PR #114 — fresh hosted + source-provenance-bound target qualification required before merge**.

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
observed_at
```

The live observer remains the authority for collecting Win32/UIA evidence. The new Control Plane adapter is data-only and cannot enumerate windows, invoke UIA, deliver input, launch a process, or authorize an action.

## Shared-kernel path

```text
accepted DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> ObservationRef(sequence N, observed_at T1)
 -> caller-declared bounded final-state expectation
 -> automatic stable process/native-window continuity predicates
 -> accepted DesktopState AFTER
 -> ObservationRef(sequence N+1, observed_at T2)
 -> require T2 > T1
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

## Observation-time freshness

A monotonically assigned adapter sequence is necessary but not sufficient evidence that the supplied Windows state was freshly observed. Without an additional time check, a caller could feed two historical `DesktopState` payloads to a new stream in order and receive sequence `N -> N+1` even though no new observation had occurred.

PR #114 therefore also requires:

```text
BEFORE.observed_at = valid timezone-aware ISO-8601 T1
AFTER.observed_at  = valid timezone-aware ISO-8601 T2
T2 > T1
```

If `T2 <= T1`, the Windows verifier returns:

```text
status = UNKNOWN
reason = stale_observation_time
```

before an otherwise matching final-state postcondition can PASS. Malformed or timezone-naive observation timestamps are rejected as invalid evidence.

This is an adapter-level additional freshness guard. The common Verification Kernel still enforces same capability/subject/stream and strictly advancing `ObservationRef.sequence`; the Windows adapter adds the capability-native time condition because it receives externally constructed `DesktopState` evidence.

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
- detects duplicate control observation fingerprints;
- requires strictly advancing timezone-aware `observed_at` for transition verification.

Digest/freshness contradictions are rejected as invalid evidence. Duplicate control fingerprints make the snapshot ambiguous; the common Verification Kernel returns `UNKNOWN`, not PASS, when unambiguous evidence is required. A non-advancing observation time also returns `UNKNOWN`, not PASS.

## Relationship to the legacy Windows verifier

`runtime/windows/verifier.py` is preserved unchanged. It belongs to the accepted Stage 26.2 foundation and is still used by historical/regression evidence.

PR #114 adds the Stage 26.3B adapter in `runtime/control_plane` rather than silently changing the semantics of the older API.

## Source provenance is part of this physical gate

PR #114 is the first release-critical target-Windows gate wired to the stronger `SOURCE_PROVENANCE_ACCEPTANCE.md` methodology.

Before the WinForms fixture starts, the PowerShell launcher independently requires an empty equivalent of:

```text
git status --porcelain=v1 --untracked-files=all
```

Then `scripts/source-provenance-gate.py` must prove on the same source root:

```text
actual HEAD == ExpectedHead
working_tree_clean == true
tracked_diff_empty == true
untracked_empty == true
all critical local files match their ExpectedHead Git blobs
qualification driver/launcher/fixture are hash-bound
relevant lockfiles are hash-bound
```

For every critical project file the provenance record keeps both its committed Git-blob identity and its exact local raw SHA-256. Evidence is written outside the source checkout so recording proof cannot dirty the source tree.

The Windows gate currently binds the shared Verification Kernel, both new Windows Control Plane adapters, accepted Windows observation/UIA/runtime files, the qualification launcher/driver/fixture, the common provenance gate itself, and `config/stage26-openadapt-lock.json`.

The overall Windows gate cannot PASS unless `SOURCE_PROVENANCE_GATE=PASS`.

## Installed OpenAdapt backend attestation

The accepted Windows resolver uses the pinned OpenAdapt Flow Windows UIA backend internally. The source-bound project lock alone does not prove which installed package bytes were actually imported on the target machine.

Therefore the physical Python driver additionally records:

```text
locked OpenAdapt repository
locked commit
locked declared version
installed openadapt-flow distribution version
version_match
actual imported openadapt_flow.backends.win_agent.server source path
SHA-256 of that imported server source file
```

Physical acceptance requires the installed distribution version to equal the locked declared version. The imported server SHA-256 is retained as target-machine provenance evidence.

This does **not** promote OpenAdapt to project verification authority. It only attests the third-party execution/observation substrate used by this Windows qualification. Project Verification Kernel semantics remain authoritative.

## Physical target qualification

The qualification reuses the accepted harmless WinForms fixture and exact PID/HWND `observe_bound_window` path.

Required final-head evidence:

```text
SOURCE_PROVENANCE_GATE=PASS
working tree / tracked diff / untracked checks all clean
installed OpenAdapt version matches the source-bound project lock
actual OpenAdapt win_agent source SHA-256 is recorded
two fresh live observations keep exact stable Windows identity
AFTER.observed_at is strictly later than BEFORE.observed_at
same-identity declared final state -> shared-kernel PASS
wrong declared final state -> FAIL
canonical synthetic process-generation drift -> FAIL
canonical synthetic HWND drift -> FAIL
stale same-snapshot observation -> UNKNOWN
non-advancing observation time -> UNKNOWN / stale_observation_time
no desktop fallback/binding ambiguity
fixture cleanup succeeds
```

Synthetic negative probes are verifier tests, not claims that the OS physically changed identity during the run. They are rebuilt through the production `build_desktop_state` path so their snapshot-local digests remain internally valid. Positive identity and time-freshness evidence comes from two fresh observations of the actual target-Windows fixture.

Harness:

```text
scripts/source-provenance-gate.py
scripts/stage26-windows-verification-qualification.ps1
scripts/stage26-windows-verification-qualification.py
```

Expected key physical output includes:

```text
SOURCE_PROVENANCE_GATE=PASS
WORKING_TREE_CLEAN=True
TRACKED_DIFF_EMPTY=True
UNTRACKED_EMPTY=True
OPENADAPT_VERSION_MATCH=True
OPENADAPT_WIN_AGENT_SERVER_SHA256=<64 hex>
SAME_LIVE_IDENTITY_PASS=True
KERNEL_PASS_STATUS=pass
WRONG_POSTCONDITION_STATUS=fail
PROCESS_GENERATION_DRIFT_STATUS=fail
HWND_DRIFT_STATUS=fail
STALE_OBSERVATION_STATUS=unknown
FIXTURE_CLEANUP_PASS=True
STAGE26_3B_WINDOWS_VERIFICATION_RESULT=PASSED
```

## Non-goals

This PR does not yet prove a natural-language Windows L3 task. It also does not implement process launch/exit verification, generic desktop action routing, or a public `desktop_*` tool.

It also does not make OpenAdapt a second verifier/AgentOS: OpenAdapt supplies existing Windows mechanics/provenance here; the project Control Plane/Verification Kernel/Finish Gate retain authority.

After this verifier is physically accepted and merged, the next acceptance slice must compose accepted Windows action/observation mechanisms into one representative Windows/application L3 task with an independent Finish Gate **and the same source-provenance discipline**. Before Stage 26.3B closes, one representative Browser L3 must also be repeated under the new provenance standard.
