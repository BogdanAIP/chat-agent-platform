# Bounded `main` self-update — Stage Research

Status: **STAGE RESEARCH — NARROW (RE-ENTERED FOR TRAY INTEGRATION)**

Research date: 2026-09-02

## Stage goal

Add one developer-machine maintenance path that checks and installs only the accepted `main` of `BogdanAIP/chat-agent-platform`, independently of any user working checkout, and expose it as one existing-tray action:

```text
Дополнительно
 -> Обновить
```

One click performs its own version check. If the installed exact accepted-main commit is already current, no installation runs and the tray reports:

```text
Обновление не требуется. Установлена последняя версия.
```

If a newer fast-forward `main` exists, the same click installs it immediately. There is no separate check button, confirmation dialog, updater window, updater desktop shortcut, periodic update polling, or new Chat-facing semantic action.

Top-level decision: **NARROW**.

Do not claim or implement release-grade package distribution, unattended installation, signed release channels, whole-install transactional rollback, or power-loss recovery; those remain Stage 27 responsibilities.

## Why the research gate was re-entered

The first brief selected a separate updater UI. During implementation the user selected a materially narrower UX: one **Обновить** item inside the existing tray. Because this changed the UI/concurrency integration boundary, Stage Research was re-entered before physical acceptance. The source/cache/install mechanism remains the same; the revised brief below covers the tray process-lifecycle interaction explicitly.

## Current project baseline and problem evidence

A real target-Windows diagnosis found a split-brain installation:

- the persistent user checkout was at `cc3fb864e83705dd4cb5453298970bd6dc76eed3`;
- its stale `origin/main` was `20d06e8311ef65ee04b9a8a940c4f0d5725de0e0`;
- the live accepted GitHub `main` was `90a8e16e6a1badecd3315968339ca691634b7ee4`;
- the installed semantic runtime advertised only the two older `procedure_run` variants;
- the installed runtime did not contain `independent_review_procedures.py` or `independent_review_state.py` even though accepted `main` did;
- exact-head qualification worktrees were current, which proved the failure was the persistent installation source rather than the new feature worktree.

Refreshing ChatGPT actions cannot repair a stale local runtime bundle. The platform needs its own local source/version path that does not treat the ordinary developer checkout as update authority.

Existing mechanisms that should be reused instead of duplicated:

- canonical install path: `scripts/bootstrap-chat-platform.ps1` plus its verified bundle installers;
- verified per-file copy: `Copy-ChatVerifiedFile`;
- existing local named-mutex pattern for single-operation ownership;
- exact detached Git worktrees already used for exact-source qualification;
- existing tray/WinForms notification surface;
- existing Start/Stop lifecycle and desired-state machinery;
- existing six-tool semantic authority boundary, unchanged by this work.

The current risk register explicitly keeps **Packaging and clean-user installation are not release-grade** open. This narrow developer-machine updater does not close that risk.

## Architecture lineage comparison

`ARCHITECTURE_REUSE_BASELINE.md` was checked before selecting the mechanism.

| Affected baseline role | Prior owner/source | Current-stage comparison | Decision |
|---|---|---|---|
| Capability authorization / consequence policy | project deterministic Control Plane | A local updater must not become Chat authority or expose arbitrary Git/command selection. It stays outside the six-tool surface. | **KEEP** |
| Capability-spanning operational state | project `WorkingState` | Update installation state is local maintenance state, not task/capability progress. Putting updater receipts into `WorkingState` would incorrectly couple product task state to installation. | **KEEP** |
| Transition verification authority | project Verification Kernel | Updater bootstrap/smoke evidence does not become task-transition authority and does not alter Kernel verdict semantics. | **KEEP** |
| Task completion authority | project independent Finish Gate | Updating the installed runtime is maintenance, not a planner task-completion claim. | **KEEP** |

No canonical baseline row currently owns **developer-machine runtime update source/materialization**, **installed-version receipt**, or **tray maintenance invocation**. Those are therefore treated as **NEW_ARCHITECTURE** for this brief and passed through the Research Scope Expansion Gate below rather than being mislabeled as a replacement of an existing baseline role.

The selected mechanism deliberately reuses existing project implementation where it exists (`bootstrap-chat-platform.ps1`, verified copy, named mutex patterns, tray UI) but does not change any baseline-selected external component or project-owned authority role. Therefore no existing baseline row becomes superseded by this PR.

## Research Scope Expansion Gate: architecture primitives and adjacent domains

| Primitive / mechanism | Direct engineering domain | Guarantee required here | Assumptions / failure boundary | Adjacent domains |
|---|---|---|---|---|
| private bare Git cache | version-control repository/materialization | update resolution is independent of stale user checkout | local filesystem and Git executable are available; not a hostile-local-user security boundary | supply-chain provenance, filesystem state |
| explicit `main` fetch refspec | Git ref synchronization | resolve only official repository `main` into one known local ref | network/GitHub may fail; failure must leave installed runtime unchanged before apply | remote-state freshness, TOCTOU |
| exact detached worktree | version-control checkout isolation | bootstrap source bytes are bound to one resolved commit, not a moving branch/dirty checkout | Git object database/worktree metadata intact | provenance, cleanup |
| ancestry gate `installed -> target` | DAG/version monotonicity | prevent automatic downgrade / rewritten-main application after a known install | prior installed SHA must remain present in cache; first install has no prior anchor | rollback policy, identity |
| strict installed-version JSON receipt | local persistence / crash consistency | distinguish currently installed accepted-main SHA from a merely checked target | process-crash durability only; no power-loss transaction claim | recovery, stale state |
| sibling-temp + replace JSON write | filesystem crash-consistency pattern | avoid partially written updater receipt on ordinary process failure | filesystem rename semantics; no fsync/power-loss guarantee claimed | persistence |
| named updater mutex | local process concurrency | exactly one updater operation at a time | cooperating local processes; abandoned mutex can be reclaimed | concurrency, duplicate effects |
| tray child-process observation | desktop UI/process lifecycle | one click delegates to fixed updater without freezing tray or granting UI install authority | tray remains alive during operation; updater owns terminal semantics | cancellation, liveness |
| tray lifecycle-busy alias | local UI concurrency | Start/Stop, double-click toggle and mode change cannot race bootstrap replacement | existing tray state machine remains authoritative for UI busy projection | race prevention |

### Scope-expansion conclusion

These primitives are narrow and local. They do **not** introduce a generic package manager, event bus, background scheduler, release registry, updater service, lease framework, or second persistence subsystem. The only new durable state is one bounded updater receipt plus Git cache metadata.

## Solution evidence

### Git exact-ref materialization

Current Git source/documentation was inspected at:

```text
git/git@1630431f326e15fcde608827b5ff38422528eb59
```

Relevant exact docs:

- `Documentation/git-fetch.adoc` documents that command-line refspecs determine what is fetched and where an explicitly mapped ref is updated; a `+` refspec explicitly permits the local tracking ref to follow a forced remote update. This is why CAP adds its **own ancestry gate** instead of treating successful fetch as permission to install.
- `Documentation/git-worktree.adoc` documents detached throwaway worktrees and separate per-worktree `HEAD`/index metadata. CAP additionally verifies `rev-parse HEAD` equals the frozen target and `status --porcelain` is clean before bootstrap.
- `Documentation/git-merge-base.adoc` documents `--is-ancestor`: exit 0 when the first commit is an ancestor of the second, 1 when not, other non-zero on error. CAP maps exactly those outcomes and fails closed on errors.

This directly supports the selected exact-source / monotonic-update mechanics.

### Mature Windows updater lessons

Exact source inspected:

```text
microsoft/vscode@359cba2f0b72a099db9d2fa502de4a2f09894908
src/vs/platform/update/electron-main/updateService.win32.ts
```

Observed relevant principles:

- explicit updater states rather than treating a click as success;
- staged download before apply;
- checksum validation before package publication;
- apply/relaunch logic separated from check/download state;
- failure/cancel paths explicitly unwind pending update state.

CAP reuses the **separation principle**, not VS Code's Squirrel/Inno package machinery, because this PR has no accepted Stage-27 package channel.

Exact source inspected:

```text
desktop/desktop@3b3cd0cecf75530d83285f494a9aba0aecf96030
app/src/ui/lib/update-store.ts
```

Observed relevant principles:

- explicit `Checking`, `Available`, `NotAvailable`, `Ready` state;
- persisted last-successful-check information;
- avoiding unsafe redundant update checks once an update is already ready.

CAP similarly persists an explicit bounded state (`current`, `update_available`, `installing`, `blocked`, `error`) and serializes updater ownership instead of inferring state from UI actions.

## Best current approaches / alternatives comparison

At least three materially distinct approaches exist for this problem.

| Approach | State / authority owner | Strengths | Failure modes / cost | Fit |
|---|---|---|---|---|
| **A. Reuse ordinary developer checkout: `git pull` then bootstrap** | user checkout + Git branch | smallest amount of new code | reproduces the observed stale checkout/origin problem; dirty branches and unrelated feature work become install authority; cannot reliably distinguish qualification worktree from persistent install source | **REJECT for updater authority** |
| **B. Private fixed-source Git cache + exact detached worktree + canonical bootstrap** | project local updater state; official `main`; existing bootstrap | resolves exact commit independently of working checkout; reuses existing installer; allows deterministic ancestry block; small implementation | Git/network dependency; bundle apply is not whole-install transactional; local Git config is not a hostile-user trust boundary | **SELECT / NARROW** |
| **C. Versioned GitHub Release/package channel with hash/signature, staged install and rollback** | release artifact metadata + installer | strongest distribution/rollback model; clean-user friendly; avoids requiring source checkout | requires release production, signing/checksum policy, package layout, rollback owner and clean-machine evidence not yet accepted | **DEFER to Stage 27** |
| **D. Download/copy individual raw GitHub files from `main`** | updater-maintained file list | no Git worktree needed | easy to miss transitive/runtime assets; many-file TOCTOU unless every file is bound to one immutable commit; duplicates canonical installer inventory and verification | **REJECT** |

Approach B is the minimum architecture that directly fixes the observed stale-checkout failure without prematurely implementing Stage 27.

## Failure lessons and shields

### Forced remote ref updates

Git permits a `+` fetch refspec to move the local tracking ref non-fast-forward. That behavior is needed so the cache accurately observes current remote `main`, but it is **not** installation permission.

Shield:

```text
known installed SHA
 -> git merge-base --is-ancestor installed target
 -> true: update may proceed
 -> false: BLOCKED
 -> command/error other than 0/1: fail closed
```

### Worktree residue

Git linked worktrees retain administrative metadata and may require `worktree remove`/`prune` after abnormal cleanup.

Shield: every normal updater path removes the exact temporary worktree in `finally` and prunes stale metadata. Residual cleanup failure is logged; it never changes the installed-version receipt.

### UI cancellation during installation

A tray process is not an installation authority. Killing the updater because the indicator closes or because a UI timer expires could interrupt canonical bootstrap mid-copy.

Shield:

- `Закрыть индикатор` refuses to exit while updater process is active;
- tray never calls `Kill()` on the updater;
- tray timer only observes terminal process exit;
- timeout/failure semantics remain inside the updater/bootstrap layer.

### Concurrent lifecycle operations

Start/Stop or mode changes during bootstrap could race runtime replacement.

Shield:

- updater has its own named single-operation mutex;
- tray refuses update while the existing lifecycle completion timer or lifecycle operation is active;
- once updater launches, its process is projected into the existing tray `OperationProcess` busy state so power toggle, double-click toggle and mode changes already reject themselves;
- manual-mode remote probe is quiesced before update and re-established from fresh visual state if still required.

### Stale or missing receipt

A pre-updater installation may have no installed-main receipt. Guessing from file timestamps or ordinary checkout state would recreate the original error.

Shield: missing receipt means **unknown installed version**, so the first updater use may reinstall current `main`; only a clean exact official-main source can publish the durable receipt.

## Fixed source and local state

Fixed production source:

```text
repository = BogdanAIP/chat-agent-platform
remote = https://github.com/BogdanAIP/chat-agent-platform.git
branch = main
```

Private local state:

```text
%LOCALAPPDATA%\ChatAgentPlatform\update-cache\repo.git
%LOCALAPPDATA%\ChatAgentPlatform\update-cache\worktrees\...
%LOCALAPPDATA%\ChatAgentPlatform\state\platform-update.json
%LOCALAPPDATA%\ChatAgentPlatform\logs\update.log
```

The public updater wrapper exposes no repository, remote URL, ref, branch, commit, command, or source-path parameter. The tray invokes only the fixed `Update` action. Internal core functions accept a remote path only so hosted tests can use a local Git fixture; that seam is not reachable through the installed tray/public updater parameter surface.

## Update algorithm

```text
Tray: Дополнительно -> Обновить
 -> ensure no tray lifecycle operation is unresolved
 -> quiesce manual health probe
 -> launch fixed public updater Action=Update in hidden child process
 -> project updater child into existing tray busy state

Updater:
 -> acquire Local\ChatAgentPlatformUpdateOperation
 -> initialize or validate private bare Git cache
 -> require exact fixed production origin URL
 -> fetch +refs/heads/main:refs/remotes/origin/main with --atomic
 -> resolve exact 40-hex target commit
 -> compare with installed accepted-main receipt
 -> if same:
      -> CURRENT
      -> perform no bootstrap
      -> tray notifies "Обновление не требуется..."
 -> if installed SHA is known:
      -> require installed is ancestor of target
      -> false: BLOCKED; no bootstrap
 -> otherwise:
      -> durable status=installing while retaining prior installed SHA
      -> create fresh detached exact target worktree
      -> verify HEAD == target and worktree clean
      -> invoke canonical bootstrap from that worktree
      -> bootstrap completes install + smoke before any success receipt
      -> updater re-runs receipt publication against the same exact worktree
      -> verify receipt == target
      -> if platform was running before update, start installed manager again
      -> return UPDATED
 -> remove exact temporary worktree

Tray:
 -> observe terminal JSON only after updater exits
 -> clear busy projection
 -> notify CURRENT / UPDATED / BLOCKED / ERROR
```

A source checkout may publish an installed-version receipt only when all are true:

- `origin` identifies the official repository;
- source `HEAD` equals exact `refs/remotes/origin/main^{commit}`;
- source worktree is clean;
- canonical bootstrap has reached its successful post-smoke receipt phase, or the already-loaded updater reconciles the same exact worktree after an older accepted bootstrap that predates this feature.

A feature branch therefore cannot become installed-main identity merely by being the branch from which a developer invoked bootstrap.

## Failure / Crash Matrix

The narrow guarantee is ordinary process/retry correctness, not power-loss transactional rollback.

| Boundary | Authoritative durable state | Possible physical state | Fresh evidence required | Retry rule / max additional effect | Shield / test |
|---|---|---|---|---|---|
| before fetch | previous receipt or none | installed runtime unchanged | none | retry allowed; zero install effects | fixed-source decision test |
| fetch/network fails | previous receipt or none | installed runtime unchanged; cache may have old objects | new successful exact fetch | retry allowed; zero install effects | fetch error is terminal error |
| target fetched, before `installing` | previous receipt | installed runtime unchanged | exact target can be re-resolved on retry | retry allowed; zero install effects | deterministic decision |
| remote `main` moved backward/rewrite vs known installed | previous installed SHA | installed runtime remains newer/different | ancestry result against newly fetched target | **blocked**; zero install effects | real local-Git forced-rollback test |
| after durable `installing`, before worktree | receipt retains previous installed SHA + target | installed runtime still previous | next exact fetch/decision | retry allowed; at most one later canonical bootstrap | state round-trip test |
| after worktree creation, before bootstrap | same `installing` state | exact source staged, installed runtime previous | exact worktree HEAD + clean status | retry allowed after cleanup; no install effect yet | worktree HEAD/clean test |
| during per-file bootstrap replacement | previous installed SHA remains authoritative | bundle may be partially replaced if bootstrap/process/power fails | successful future bootstrap + smoke; no inference from partial files | fail closed; retry bootstrap; whole-install rollback explicitly not claimed | existing verified-copy/bootstrap tests; Stage 27 owns stronger transaction |
| bootstrap fails | previous installed SHA remains authoritative unless no truthful receipt existed | runtime may be stopped / partially refreshed | successful subsequent bootstrap/smoke | retry allowed; no success claim | wrapper error state; no new current receipt |
| bootstrap succeeds, before wrapper reconciliation | bootstrap may already have exact target receipt, or previous accepted bootstrap may not know updater | installed target bundle is present | `Publish-CapInstalledVersionFromSource` on same exact worktree + receipt reread | reconciliation only; no second bootstrap required in same run | explicit post-bootstrap reconciliation |
| receipt target committed, before optional restart | target installed SHA authoritative | new runtime installed but stopped | installed command Start result | no reinstall; at most one Start attempt in this run | restart branch tests/source review |
| restart fails | target installed SHA remains truthful; updater status becomes error | new runtime installed, desired service may be stopped | separate manager status/start | do not downgrade/reinstall automatically; operator retry Start/update | error state preserves installed SHA |
| updater process exits before tray consumes result | receipt/updater state authoritative | operation already terminal | child exit + structured stdout or state/log | tray must not replay update automatically | tray observes once; no background retry |
| duplicate tray click / second updater | first process + named mutex authoritative | first update may be active | process/mutex ownership | duplicate effect prohibited; second caller rejected | busy state + named mutex |
| tray close while updater active | updater process authoritative | installation may be in progress | updater child still running | tray close blocked; zero cancellation effects | source contract asserts no `Kill()` |
| power loss during bundle replacement | previous or target receipt may not fully describe partially copied bundle | partial installation possible | **outside narrow guarantee** | no automatic claim; Stage 27 required for transactional rollback | explicit non-goal / release risk remains open |

No release-critical cell required by the selected **NARROW** guarantee remains unknown. The power-loss/whole-install transaction cell is explicitly outside the selected goal and therefore does not masquerade as a supported guarantee.

## Security / authority boundary

The updater is not a generic Git or execution surface:

```text
user authority = click "Обновить"
tray adapter = fixed Action=Update
remote authority = fixed official repository main only
installer authority = fixed scripts/bootstrap-chat-platform.ps1 from exact fetched target
Chat semantic authority = unchanged six-tool surface
```

No tray request field can select another repository, URL, ref, path, executable, PowerShell body, or command.

This mechanism does not attempt to defend against a hostile same-user Windows environment that can already replace `%LOCALAPPDATA%` files, Git executable/config, or the running scripts. Stage 27 package/signature work is the place to establish a stronger distribution trust model.

## Must-have mechanisms now

- fixed official `main` source;
- private cache independent of ordinary checkout;
- exact explicit fetch/ref resolution;
- exact detached clean worktree;
- known-installed ancestry gate;
- strict installed-version receipt;
- one updater mutex;
- canonical bootstrap reuse;
- exact receipt reconciliation after bootstrap;
- one tray **Обновить** action with no confirmation/check UI;
- no tray cancellation of active updater;
- serialization against tray Start/Stop/mode operations;
- exact-head hosted CI + target-Windows physical gate + fresh semantic review.

## Explicitly deferred / rejected

Deferred to Stage 27:

- versioned release package/channel;
- artifact signature policy;
- clean-machine install/update;
- whole-install transactional rollback;
- power-loss recovery;
- unattended/background update scheduling.

Rejected for this slice:

- ordinary checkout as update authority;
- raw per-file GitHub sync;
- arbitrary repository/ref/path parameters;
- separate updater window;
- updater desktop shortcut;
- periodic update polling;
- new Chat-facing tool/procedure.

No baseline role required by this stage remains lineage-`DEFER`; deferred items are outside the narrowed stage goal.

## Verification plan

Hosted acceptance must prove at minimum:

- all changed/new PowerShell parses;
- public updater is fixed to official `main` and exposes no arbitrary source parameters;
- exact fetch returns fixture `main` SHA;
- fixture fast-forward is accepted;
- forced remote rollback is rejected;
- detached worktree HEAD equals exact target and is clean;
- update-state round trip is strict;
- bootstrap installs updater core/wrapper/tray helper and records version only after smoke phase;
- tray registers exactly one user update action named **Обновить** under `Дополнительно`;
- tray invokes `Update`, not a separate visible `Check`/confirmation flow;
- CURRENT produces the exact no-update notification;
- tray never calls `Kill()` on the updater;
- active update blocks tray exit and lifecycle/mode mutations;
- existing six-tool/public semantic contracts remain unchanged.

Physical target-Windows acceptance must prove on exact PR bytes:

1. the **Обновить** entry appears under the existing `Дополнительно` submenu;
2. one click starts the fixed-source updater without PowerShell/user command entry;
3. fixed source resolves official accepted `main`, never the PR branch;
4. if target equals installed receipt, no bootstrap runs and the expected no-update notification appears;
5. for an actual accepted-main transition when available/fixture-qualified, installation uses an exact detached target and reaches the expected installed receipt;
6. a running platform is returned to running after successful update;
7. no duplicate update is possible from repeated clicks;
8. no tray close/lifecycle action can terminate or race active update.

The mandatory fresh ordinary-Chat semantic review then reviews the exact final BASE..HEAD and this physical/CI evidence. Any material code change invalidates that review/evidence as required by repository policy.

## Falsification triggers

Reconsider the architecture instead of merging if any of these occurs:

- current `main` can be installed from a dirty/moving/user checkout;
- PR/feature branch can become update authority;
- a known installed SHA can be downgraded automatically;
- two updater calls can execute bootstrap concurrently;
- tray can terminate an active updater;
- updater can race Start/Stop or mode mutation;
- bootstrap success can be reported without exact target receipt;
- existing six-tool authority changes;
- target-Windows physical use requires manual PowerShell after the feature is installed;
- reliable recovery requires a whole-install transaction rather than the explicitly narrowed process-retry guarantee.

## Complexity budget

New production pieces:

- one small Git/source/state core script;
- one fixed public updater wrapper;
- one thin tray adapter;
- one strict local JSON receipt;
- one private bare Git cache/worktree root;
- focused tests and this research brief.

No new daemon, scheduler, service, database, plugin framework, public semantic tool, package format or release process is introduced.

This does add local maintenance infrastructure, but it replaces a demonstrated repeated manual burden and, more importantly, removes the ordinary developer checkout from installation freshness authority. The selected design is intentionally an interim developer-machine path that Stage 27 may later refine/replace with a release-grade package channel.

## Final architecture decision

**NARROW — PRODUCTION IMPLEMENTATION MAY CONTINUE.**

Selected mechanism:

```text
fixed official main
 -> private Git cache
 -> exact target SHA
 -> ancestry guard
 -> exact detached clean worktree
 -> existing canonical bootstrap
 -> exact installed receipt
 -> optional restart to preserved pre-update running intent
 -> one existing-tray notification flow
```

Durable invariants preserved:

- public Chat semantic inventory remains exactly six tools;
- updater cannot widen Chat capability authority;
- no PR/feature branch is production update authority;
- known installed version never automatically moves backward;
- UI success is not installation truth; exact receipt/bootstrap result is;
- no active update is cancelled by the tray;
- release-grade update/rollback remains explicitly unclaimed until Stage 27.
