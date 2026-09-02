# Bounded `main` self-update — Stage Research

Status: **STAGE RESEARCH — NARROW**

Research date: 2026-09-02

## Decision

**NARROW**: implement one developer-machine maintenance path that checks and installs only the accepted `main` of `BogdanAIP/chat-agent-platform`, independently of any user working checkout. Do not claim or implement release-grade package distribution, unattended background installation, signed release channels, or whole-install rollback; those remain Stage 27 responsibilities.

## Trigger / problem evidence

A real target-Windows diagnosis found a split-brain installation:

- the persistent user checkout was at `cc3fb864e83705dd4cb5453298970bd6dc76eed3`;
- its stale `origin/main` was `20d06e8311ef65ee04b9a8a940c4f0d5725de0e0`;
- the live accepted GitHub `main` was `90a8e16e6a1badecd3315968339ca691634b7ee4`;
- the installed semantic runtime advertised only the two older `procedure_run` variants;
- the installed runtime did not contain `independent_review_procedures.py` or `independent_review_state.py` even though accepted `main` did;
- exact-head qualification worktrees were current, which proved the failure was the persistent installation source rather than the new feature worktree.

Therefore an "update actions" refresh in ChatGPT cannot repair a stale local binary/runtime bundle. The local platform needs its own source/version check that does not trust the user's ordinary checkout.

## Goal

Provide a visible Windows update button that can:

1. show the exact installed accepted-main commit when known;
2. fetch the current official `main` into a private service cache;
3. report current / update available / blocked / error;
4. install only an exact fetched `main` commit;
5. preserve a running platform intent by restarting the installed runtime after a successful update;
6. never require the user to type PowerShell for routine checks/updates.

The first UI is a dedicated desktop shortcut `Обновить Chat Agent Platform` opening a small Windows dialog with explicit **Проверить обновление** and **Обновить** buttons. This avoids changing the large existing tray state machine in the same maintenance slice. The same updater core may be reused by a later tray menu without changing update authority.

## Explicit non-goals

- no PR / feature-branch update source;
- no caller-supplied repository, URL, ref, branch, commit, command, or filesystem source;
- no automatic background installation;
- no new Chat-facing semantic tool or procedure;
- no GitHub credential in the updater;
- no clean-machine package manager;
- no release asset/signature framework;
- no claim of atomic whole-application rollback;
- no power-loss transactional guarantee;
- no automatic ChatGPT product-side action-schema refresh.

## Architecture lineage

| Role | Existing owner | Decision | Reason |
|---|---|---|---|
| platform installation | `bootstrap-chat-platform.ps1` + verified bundle installers | **REUSE_MORE** | updater calls the canonical bootstrap instead of creating a second installer |
| copied-file integrity | `Copy-ChatVerifiedFile` | **REUSE_MORE** | existing source-to-temp SHA-256 verification remains authoritative for installed text/runtime assets |
| lifecycle serialization | local named mutex pattern | **REUSE_MORE** | updater receives its own one-operation mutex while existing manager lifecycle mutex still owns Start/Stop |
| exact-source qualification | exact detached Git worktrees already used by physical gates | **REUSE_MORE** | updater uses the same exact-commit/clean-worktree shape for source identity |
| public semantic authority | six canonical tools | **KEEP** | updater is a local maintenance UI, not Chat authority |
| release-grade update / rollback | Stage 27 Distribution & Maintenance | **KEEP** | this slice deliberately does not pull that stage forward |

New local roles are limited to a private Git update cache and one version/check state receipt.

## Selected source and state

Fixed source:

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

The public updater wrapper exposes only `Check | Update`. Test-only/internal core functions accept a remote path so hosted tests can use a local Git fixture; the installed/public command does not expose that parameter.

## Update algorithm

```text
Check / Update
 -> acquire Local\ChatAgentPlatformUpdateOperation
 -> initialize or validate private bare Git cache
 -> require exact fixed origin URL
 -> fetch +refs/heads/main:refs/remotes/origin/main with --atomic
 -> resolve exact 40-hex target commit
 -> compare with installed accepted-main receipt
 -> if same: CURRENT
 -> if installed is known: require installed commit is ancestor of target
      -> false: BLOCKED (no downgrade / rewritten-main install)
 -> for Update only:
      -> durable status=installing while retaining prior installed SHA
      -> create fresh detached exact target worktree
      -> verify HEAD == target and worktree clean
      -> invoke canonical bootstrap from that worktree
      -> bootstrap must finish all install + smoke work before publishing exact installed-version receipt
      -> verify receipt == target
      -> restart platform only when desired state was running before update
 -> remove temporary worktree
```

A source checkout publishes an installed-version receipt only when all are true:

- `origin` identifies the official repository;
- source `HEAD` is exact `refs/remotes/origin/main`;
- source worktree is clean;
- canonical bootstrap reached its final successful phase.

A feature branch therefore cannot become authoritative installed-main identity merely by running bootstrap.

## Persistence / recovery matrix

| Interruption / state | Result | Retry rule |
|---|---|---|
| check/fetch fails before install | installed app unchanged; error only | retry allowed |
| target resolved, process dies before worktree/install | installed app unchanged | retry allowed |
| remote `main` is not descendant of known installed SHA | update blocked before bootstrap | operator/repository investigation required |
| process dies with state=`installing` before bootstrap completes | previous installed SHA remains recorded | retry exact/newer fast-forward target allowed |
| bootstrap fails | no new success receipt; updater fails closed | retry is allowed; no release-grade rollback claim |
| bootstrap succeeds but wrapper dies before reading receipt | bootstrap already wrote exact receipt | next check reconciles from receipt |
| platform restart fails after successful install | installed SHA remains truthful; status/error reports restart failure | retry Start separately / investigate |
| concurrent updater | second updater blocked by named mutex | retry after owner exits |
| stale user checkout | irrelevant to updater source | private cache resolves official `main` |
| power loss during bundle replacement | outside narrow guarantee | Stage 27 owns release-grade rollback/recovery |

The existing risk "Packaging and clean-user installation are not release-grade" remains open; this feature is not its close condition.

## Direct mechanism evidence

Primary Git mechanisms used by the implementation:

- `git fetch` with an explicit refspec provides the exact `main` ref update; `--atomic` makes the requested ref update all-or-nothing for that fetch operation.
- `git worktree add --detach <path> <commit>` provides an exact detached source checkout.
- `git merge-base --is-ancestor <installed> <target>` provides the ancestry predicate used to reject a remote rollback/non-fast-forward target.

These mechanics establish source/ref/ancestry identity. They do not make copying the entire installed application power-loss transactional, and this research does not claim that.

## Public source-code research

### VS Code

Exact source inspected:

```text
microsoft/vscode@359cba2f0b72a099db9d2fa502de4a2f09894908
src/vs/platform/update/electron-main/updateService.win32.ts
```

Observed reusable principle: Windows update handling separates update states and stages download to a temporary path, checks the configured SHA-256 before publication, then transitions to apply/ready state. This supports keeping **check identity**, **staged source**, **verification**, and **apply** distinct. Its Squirrel/package infrastructure is not reused because CAP has no accepted Stage-27 package channel yet.

Decision: **KEEP principle / do not port framework**.

### GitHub Desktop

Exact source inspected:

```text
desktop/desktop@3b3cd0cecf75530d83285f494a9aba0aecf96030
app/src/ui/lib/update-store.ts
```

Observed reusable principle: explicit states distinguish checking, available, not available, and ready; the last successful check is persisted, and re-check is suppressed in an already-ready state to avoid Windows updater hazards. CAP similarly persists explicit current/update-available/installing/blocked/error state rather than inferring success from a button click.

Decision: **KEEP state-machine principle / do not port Electron updater**.

## Security boundary

The updater is not a generic Git or execution surface:

```text
user authority = Check | Update
remote authority = fixed official repository main only
installer authority = fixed scripts/bootstrap-chat-platform.ps1 from exact fetched target
```

No request field can select another repository, URL, ref, path, executable, PowerShell body, or command. The private core's injectable remote is an internal hosted-test seam and is not reachable through the installed UI parameters.

## Acceptance plan

Hosted acceptance must prove at minimum:

- all new PowerShell parses;
- public updater source is fixed to official `main`;
- exact fetch returns the fixture main SHA;
- a fixture fast-forward is accepted;
- a forced remote rollback is rejected;
- detached worktree HEAD equals exact target and is clean;
- update-state round trip is strict;
- bootstrap installs updater core/wrapper/UI and publishes version only after smoke phase;
- UI has explicit check and confirmed update actions;
- existing six-tool/public semantic contracts remain unchanged.

Because this changes installed runtime maintenance and can stop/restart the live semantic route, hosted CI is necessary but not sufficient. Before merge, run a target-Windows physical update qualification from an intentionally stale installed accepted-main build to the exact PR head or, if installing a PR head would violate the official-main-only boundary, use a local fixture/accepted-main transition that proves the exact same installed updater bytes and then perform the repository's mandatory fresh ordinary-Chat semantic review on the exact head.
