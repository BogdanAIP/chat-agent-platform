# General Computer-Use Coverage — Stage Research

Status: **STAGE RESEARCH — NARROW (qualification architecture only)**

Research date: 2026-09-22.

## Stage question

What is the minimum finite, release-critical qualification architecture that can
materially broaden CAP's already accepted Browser + Windows/Desktop scope across real
application families without introducing a second planner, a generic desktop AgentOS,
or new consequence authority merely to run more tests?

The product outcome is a characterized cross-application evidence matrix, not a claim
of universal Windows accuracy.

This stage follows the reviewer-reuse stage in `ROADMAP.md`. PR #159 has not yet
completed its required target-Windows physical reviewer gate, so this branch may
prepare the next stage and its qualification mechanics in parallel, but it must not
claim that the roadmap prerequisite or this stage is accepted before those physical
gates exist.

## Current project baseline

Already accepted mechanisms include:

- project-owned typed Windows runtime;
- `DesktopState` with exact PID/HWND/native identity and freshness;
- structure-first UIA/native observation/action with bounded local-vision fallback;
- project Browser semantics backed by Playwright;
- Browser DOM/accessibility observation plus bounded vision escalation;
- shared Verification Kernel / `PASS | FAIL | UNKNOWN`;
- independent Finish Gate;
- exact source/install/runtime provenance where the qualification depends on exact
  executing bytes;
- WorkingState/reconciliation for the already declared production consumer.

Accepted physical evidence already proves representative Browser and Windows vertical
tasks, but `EVIDENCE_INDEX.md` explicitly does **not** claim broad
Windows/Browser/Electron/Office reliability.

The public semantic surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

No new public tool is required merely because the acceptance matrix becomes broader.

### Current public desktop-route gap (2026-09-25 re-entry)

The current `semantic-control-plane-projection.mjs` admits only five fixed
`procedure_run` schemas. Of those, `windows_case_update_v1` controls only the
prepared Case Desk; `workspace_write` changes file bytes without operating an
application. The physical VS Code edit was run by an isolated qualification
harness, not by the ordinary-Chat public route. The unmerged Core head
`ca6923924952a2f457dc12e3604c97034a8fae23` adds binding to the fixed
Windows procedure, but does not register a Notepad, Electron, Office or dialog
procedure. The unreviewed Native Host head
`68b15d831b3e4f17c1781d0016ea44a8273e4ec3` does not supply one either.

Therefore a matrix harness can measure internal Windows primitives, but it
cannot count Notepad/Electron/Office/dialog actions as **ordinary-Chat product
tasks** until those actions have a separate, reviewed public consequence
contract. Keeping the inventory at six tools does not make a new registered
procedure or widened `procedure_run` schema authority-neutral. Such a route
needs its own Stage Research, exact target/operation binding, effect and
ambiguous-delivery handling, review and target-Windows qualification. Until
then those product-route rows are `UNSUPPORTED` and the broad gate stays open.

The smallest candidate for that separate decision is one pre-opened disposable
text file in Notepad: insert an exact bounded line into the intended window,
Save once, independently compare the file bytes and confirm a similar decoy
window/file was untouched. Bind the target file and PID/HWND/process generation
outside model-supplied arguments; reject an unverified unsaved buffer, stale
window, changed focus or unexpected dialog. Start with the existing
window-scoped UIA/guarded-input route; inspect the installed Notepad control
tree before choosing a text action. Defer Save As, arbitrary paths and general
desktop clicks. This is a candidate task contract, **not** implementation
authority or a completed physical test.

## Architecture lineage comparison

| Role | Prior owner/source | Decision for this stage | Reason |
|---|---|---|---|
| Browser semantic execution | project Browser capability + Playwright | **KEEP** | Already accepted; broad coverage should first measure it rather than replace it. |
| Browser structure -> vision fallback | project bounded vision route | **KEEP** | Existing state-first fallback is exactly the required assurance shape. |
| Windows/Desktop observation + actuation | project typed Windows runtime + UIA/Win32 | **KEEP** | Existing PID/HWND/native identity and bounded actions preserve project authority. |
| Microsoft `winapp ui` mechanics | public WinApp UI Automation CLI/library | **DEFER as focused provider candidate** | Real inspect/invoke/set-value/input mechanics exist, but no measured CAP gap warrants replacing the accepted Windows route. A later adapter must keep CAP identity, authorization and verification. |
| Selective Office/native mechanics | UFO/UFO²-derived UIA/Win32/WinCOM ideas behind focused adapters | **REFINE / only on measured gap** | Reuse app-native mechanics when they materially improve one proven gap; do not import UFO planner/AgentOS authority. |
| Authenticated real-browser operation | BrowserSkill research in PR #161 | **DEFER from first matrix; TRACKED** | Valuable for logged-in Chromium, but current PR #161 records an unresolved local peer-authentication boundary for production authority. |
| Windows UIA wrapper alternative | FlaUI / native UIA ecosystem | **DEFER / gap candidate** | Mature wrapper family may reduce low-level UIA custom code if an existing CAP path exposes a measured control-model gap. |
| RPA workflow engine | Power Automate Desktop | **REJECT as first-stage runtime owner** | Broad mature automation exists, but it introduces a separate flow/runtime product and authority model; use its documented failure modes as test evidence rather than making it CAP authority. |
| Electron-specific browser automation | Playwright Electron support | **DEFER / comparison only** | Current Playwright documentation still marks Electron automation experimental and it normally assumes app launch ownership. Existing Windows/UIA should be measured first for already-running Electron apps. |
| Procedure capture/replay | OpenAdapt | **DEFER to the next roadmap stage** | Procedure integration follows this coverage gate and must not be pulled forward merely to run app tests. |

### Correction to the earlier `winapp CLI` exclusion (2026-09-25)

The older statement that `winapp CLI` is only an application-development CLI
and cannot automate desktop UI is false. Microsoft also ships `winapp ui` for
UIA-backed inspection and interaction with running applications, plus the
`Microsoft.Windows.SDK.BuildTools.WinApp.UIAutomation` library. The CLI can
target an explicit HWND, search controls, invoke a pattern, set a value or send
keys. Documentation: https://learn.microsoft.com/en-us/windows/apps/dev-tools/winapp-cli/ui-automation

Source-code evidence, inspected at `microsoft/winappCli`
`8158d14f8940e1a23d972e729e1dcce84de423ef`:

- `src/winapp-CLI/WinApp.Cli/Commands/UiCommand.cs` registers the actual `ui`
  commands. `UiSetValueCommand.cs` resolves the requested app/HWND, finds the
  control, then calls `UiAutomationService.SetValueAsync`; that method checks
  whether the control is still present before applying its UIA value strategy.
- `WinApp.UIAutomation/Services/UiTargetResolver.cs` can bind an explicit HWND,
  but an app/title with several windows auto-selects the foreground or largest
  window. CAP must not inherit this heuristic for a consequence action.
- `WinApp.UIAutomation/Services/UiAutomationService.cs` offers
  `FindSingleElementAsync(..., requireUnique: true, ...)` and explicit pattern
  invocation. `WinApp.UIAutomation.Tests/RealUiAutomationTests.ExplicitQueries.cs`
  and `.ExplicitIdentity.cs` cover explicit-window isolation, stale-source
  refusal, ambiguous matches and no invocation on identity failure.
- `WinApp.Cli/Commands/UiSendKeysCommand.cs` re-resolves the element and checks
  the target process/window, but its default PostMessage transport can warn
  about silent non-delivery to XAML controls. CLI exit code is delivery evidence,
  not CAP verification of the application effect.

Classification: `OPEN_IMPLEMENTED`, `REFERENCE_ONLY` for this qualification
slice. Re-evaluate library reuse through a narrow adapter only after a measured
Notepad/other-app gap. Do not expose raw `winapp ui` commands or transfer CAP
authorization, file identity, `PASS` or `DONE` to this provider.

## Current external evidence

### Microsoft UI Automation

Microsoft documents UI Automation as the Windows accessibility/test automation
framework providing programmatic access to most desktop UI elements and control
patterns.

Sources:

- https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32
- https://learn.microsoft.com/en-us/windows/win32/winauto/ui-automation-specification
- https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-clientsoverview

Implication for CAP: the current UIA-first Windows design remains the strongest default
for native, Electron-accessibility and common dialog coverage. The matrix must still
test dynamic tree changes, focus/foreground behavior and controls that do not expose
usable UIA patterns.

### Power Automate Desktop failure evidence

Microsoft documents both mature selector-based desktop UI automation and practical
limitations:

- UI actions can depend on foreground/focus;
- simulated actions are unsupported for multiple control/framework combinations;
- element detection can fail with incompatible frameworks/background interference;
- elevated-app interaction changes the security boundary.

Sources:

- https://learn.microsoft.com/en-us/power-automate/desktop-flows/desktop-automation
- https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/uiautomation
- https://learn.microsoft.com/en-us/troubleshoot/power-platform/power-automate/desktop-flows/ui-automation/element-picker-cant-see-elements
- https://learn.microsoft.com/en-us/power-automate/desktop-flows/how-to/enable-ui-access

Implication for CAP: focus, elevation, unsupported-control and selector ambiguity are
real failure classes and belong in our qualification matrix even though CAP does not
adopt Power Automate as its runtime.

### UFO²

Current Microsoft UFO² documentation describes a hybrid Windows stack using UIA,
Win32, WinCOM, application-specific APIs and visual control detection across many
applications.

Sources:

- https://github.com/microsoft/UFO
- https://github.com/microsoft/UFO/blob/main/documents/docs/ufo2/overview.md
- https://github.com/microsoft/UFO/blob/main/documents/docs/mcp/overview.md

Useful role: selective Windows/Office mechanics.

Rejected role: UFO HostAgent/AppAgent/Galaxy planning, model routing and completion
authority. Ordinary ChatGPT remains CAP's only general planner and project
Verification/Finish Gate remain authoritative.

### FlaUI

FlaUI is a maintained .NET wrapper over native Microsoft UI Automation for Win32,
WinForms, WPF and Store applications. Its maintainer stated in 2026 that the project
remains active, although maintenance capacity is limited.

Sources:

- https://github.com/FlaUI/FlaUI
- https://github.com/FlaUI/FlaUI/issues/724
- https://github.com/FlaUI/FlaUI.WebDriver

Useful role: a future focused UIA provider/wrapper if direct CAP UIA mechanics show a
measured gap. There is no evidence yet that replacing current accepted CAP Windows
mechanics with FlaUI improves this stage.

### Browser / BrowserSkill

The accepted Browser default remains project semantics backed by Playwright.

BrowserSkill 0.3.0 adds real logged-in browser operation, full-page screenshots,
remote mode, audit features and user-tab borrow/return. PR #161 separately researches
it as a future Browser provider while recording a peer-authentication blocker for
production logged-in-profile authority.

Sources:

- https://github.com/Tencent/BrowserSkill
- https://github.com/Tencent/BrowserSkill/releases
- https://github.com/Tencent/BrowserSkill/blob/main/CHANGELOG.md

Decision here: do not make the broad first matrix depend on BrowserSkill. Its
authenticated-browser slice remains a tracked later Browser variant once the security
boundary is closed.

### Electron

Playwright documents Electron support as experimental:

- https://playwright.dev/docs/api/class-electron

Because that route normally launches/owns the Electron application process, it is not
automatically the right fit for CAP's real already-running desktop application
boundary. The first Electron rows should therefore exercise the normal Windows/UIA
path; a separate Electron-native adapter is justified only by measured failures.

## Architecture primitives introduced by this stage

The first slice intentionally introduces **no new consequence-bearing runtime
primitive**.

It adds only qualification/test concepts:

1. a finite immutable matrix manifest;
2. a per-case qualification identity;
3. BEFORE / action / AFTER evidence references using existing capability-native
   observations;
4. deterministic expected-effect and Finish-Gate result recording;
5. exact runtime/source provenance references;
6. bounded environmental-variant classification.

The matrix manifest is test/acceptance configuration, not capability authority. It
cannot grant an action, choose a new backend, broaden an origin or application scope,
or convert provider success into project `PASS`/`DONE`.

If implementation discovers that a new provider/session/persistence/retry/concurrency
mechanism is required, production work stops and Stage Research re-enters before that
mechanism is added.

## Materially distinct approaches

### A. Replace the desktop/browser substrate with one general external AgentOS/RPA — REJECT

Examples include importing UFO² orchestration or adopting Power Automate as the
top-level computer-use owner.

Strength: broad ready-made application support.

Failure: it duplicates/replaces CAP planning, authority, effect verification and
completion ownership; provider task success is not project Finish-Gate success.

### B. Build new CAP-specific adapters for every application — REJECT

Strength: maximal local control.

Failure: high maintenance, duplicates mature UIA/WinCOM/browser mechanics and scales
poorly. It directly conflicts with the repository reuse-first direction.

### C. Keep existing CAP capability owners; measure breadth; add only focused providers for measured gaps — SELECT

```text
ordinary ChatGPT
 -> existing CAP semantic surface
 -> project Control Plane / Verification / Finish Gate
 -> existing Browser or Windows capability
 -> existing provider first
 -> optional focused mature provider only for a reproduced gap
```

This preserves the accepted trust boundary, uses the broad matrix to discover real
gaps, and prevents a candidate technology from becoming architecture simply because
it has more features.

For Windows, the first provider remains the accepted window-scoped UIA route.
`winapp ui` is an implemented alternative for a measured app-specific gap, not
evidence that CAP already exposes a public desktop action or verifies Save.

### D. Make the first coverage gate depend on BrowserSkill/UFO/OpenAdapt simultaneously — REJECT

This would conflate three independent roadmap/research questions and make failures
impossible to attribute. BrowserSkill remains separate PR #161 research; OpenAdapt
belongs to the following external-procedure stage; UFO mechanics may be pulled only
for one measured Windows/Office gap.

## Finite acceptance matrix

The gate is intentionally finite. It has five application families and five
environmental variants.

### Application families

1. **Native Windows / Win32-like**
   - two distinct installed applications;
   - at least one standard edit/save flow;
   - at least one control-selection/state-change flow.

2. **Browser**
   - two distinct browser tasks through the accepted Playwright/project route;
   - one DOM/accessibility-dominant;
   - one requiring the already reviewed structure-to-vision escalation boundary.

3. **Electron**
   - two distinct Electron application tasks where UIA/native state is available;
   - first route is the existing Windows/Desktop capability, not Playwright Electron.

4. **Office-style**
   - two document/spreadsheet-style tasks in distinct applications or distinct native
     control families;
   - first route is normal UIA/native CAP behavior;
   - one measured gap may justify a focused WinCOM/UFO-derived adapter re-entry.

5. **Standard file/dialog**
   - Open/Save-As/file-picker flow;
   - overwrite/cancel or similarly consequence-sensitive dialog flow;
   - verify target path and absence of unintended sibling/decoy effects.

Exact application names are frozen in the qualification manifest before physical
execution. Selection is based on what is actually installed/supported on the target
machine; changing an app after a failure creates a new manifest/version rather than
silently replacing the failed row.

### Environmental variants

Every family must cover its normal case plus a bounded selection from:

- non-default DPI/scaling;
- moved/resized window;
- focus loss / foreground change;
- similar windows or decoy records;
- unexpected dialog/overlay/noise.

The overall manifest must contain every variant at least twice across distinct
application families. The same row may cover more than one variant when the resulting
failure attribution remains unambiguous.

## Per-case acceptance contract

Each physical case binds:

```text
matrix_version
case_id
application_family
application_identity
provider/runtime identity
variant set
BEFORE observation
authorized bounded action(s)
ExpectedEffect
AFTER fresh observation
Verification Kernel result
independent Finish Gate
target-only mutation / decoy invariants
source/install/runtime provenance
cleanup result
```

Required result dimensions remain separate:

```text
task_success = PASS | FAIL | UNKNOWN
safety_policy = PASS | FAIL | UNKNOWN
finish_gate = DONE | NOT_DONE | UNKNOWN
```

A provider/app reporting success never substitutes for project verification.

## Failure matrix

| Boundary/failure | Required behavior |
|---|---|
| target app/process/window not uniquely identified | zero consequence action; `UNKNOWN`/ABSTAIN |
| target becomes stale or HWND/process generation changes before action | re-observe; no action under stale identity |
| focus changes before physical input | revalidate target/focus or fail closed |
| similar/decoy window matches weak selector | no action until exact identity discriminates it |
| app-name lookup silently selects foreground/largest window | require CAP-bound exact PID/HWND/generation before any provider action |
| unexpected modal/dialog/overlay appears | classify from fresh observation; no blind click-through |
| structure/UIA lacks required target | use only already-authorized bounded vision fallback; otherwise ABSTAIN |
| vision proposes target that disagrees with stronger native state | native/state evidence wins; no action |
| action acknowledgement missing | fresh re-observe; never infer success from delivery |
| provider reports successful input but control ignores it | independently observe the expected UI/file effect; otherwise `UNKNOWN` |
| effect ambiguous | project `UNKNOWN`; no blind duplicate effect |
| application exits/restarts | old process/HWND evidence invalid; bind new identity only through a new admitted attempt |
| provider/runtime provenance mismatch | qualification invalid regardless of apparent task success |
| cleanup cannot prove test fixture/target state | case does not count as accepted evidence |
| new external provider would be required | stop that implementation path and re-enter Stage Research |

## Failure shields

The qualification implementation must prove:

1. no action occurs from stale/wrong PID/HWND/DOM identity;
2. focus loss and decoy-window cases cannot redirect the consequence;
3. delivery/ack is never counted as verified effect;
4. structure-to-vision escalation is explicit and does not silently override stronger
   state;
5. exact executing source/runtime provenance is captured for release-critical rows;
6. every case has an independent task-level Finish Gate;
7. failure/unknown rows remain evidence and are not silently substituted by another
   application;
8. the manifest is finite and versioned before physical execution.

## Acceptance ladder

### L1 — deterministic qualification contract

- schema/manifest validation;
- duplicate case-id rejection;
- immutable case definition/hash;
- expected-effect/result dimensionality;
- provenance fields;
- fail-closed unknown/missing evidence;
- no provider success -> Finish Gate shortcut.

### L2 — hosted/synthetic integration

- existing Browser and Windows test fixtures;
- decoy/stale/focus/modal simulations;
- structure-miss -> bounded vision route;
- wrong-provider/runtime-provenance rejection;
- matrix aggregation without hiding failed rows.

### L3 — target Windows physical matrix

- exact reviewed unchanged qualification head;
- manifest frozen before execution;
- all five application families represented as defined above;
- every environmental variant represented at least twice;
- exact per-row evidence retained;
- no unresolved `UNKNOWN` in a row claimed as accepted;
- failures are characterized rather than replaced;
- broad scope is accepted only if materially broader than #113/#115/#118 evidence.

Passing the stage does **not** claim universal application reliability.

## Decision

**NARROW**

Proceed with a qualification-first slice:

1. define/version the matrix manifest and result contract;
2. reuse the existing Browser/Windows capability owners unchanged;
3. build deterministic L1/L2 matrix aggregation and adversarial fixtures;
4. do not adopt a new desktop/browser provider before a reproduced matrix gap;
5. when the target laptop is available, freeze exact app names and execute the
   physical L3 matrix;
6. re-enter Stage Research for any material provider/authority/persistence mechanism
   needed to close a measured gap.

The Notepad candidate and other presently unsupported product-route rows are
**DEFERRED as public desktop authority** within this qualification-only decision.
Re-entry requires a concrete bounded public contract and evidence about the
installed app's control tree, identity and ambiguous Save outcomes. The L1/L2
manifest and fixtures may proceed; they cannot substitute for the absent public
route, independent review or the target-Windows L3 gate.

Do not pull forward the external-procedure stage, persistent sessions, a generic
provider framework, UFO AgentOS, Power Automate runtime ownership, arbitrary local
execution, or broad authenticated-browser authority.
