# Technical Debt Register

Status: **CURRENT MAINTENANCE REGISTER**.

This file tracks implementation/process compromises that already exist and should eventually be removed, hardened or simplified.

It is narrower than `KNOWN_ISSUES.md`, `PROJECT_RISKS.md` and `ROADMAP.md`:

- `TECH_DEBT.md` = existing compromise/maintenance debt;
- `KNOWN_ISSUES.md` = broader current limitations/issues;
- `PROJECT_RISKS.md` = ranked risks to project success;
- `ROADMAP.md` = planned capability work.

A missing future capability is **not** technical debt merely because it is unfinished. Always resolve live `main` and active PR heads before acting.

## Priority scale

```text
P0 = current safety/correctness critical path
P1 = remove before stable release unless stronger evidence justifies deferral
P2 = important hardening/cleanup; schedule when owning subsystem is touched
P3 = repository/process hygiene; batch into maintenance sweeps
```

## Open debt

| ID | Priority | Debt | Why it is debt | Intended close point | Close condition |
|---|---:|---|---|---|---|
| TD-001 | **P0** | Browser network policy is not a complete DNS/redirect/private-network boundary | Current Browser policy is intentionally narrower than a full network sandbox. Wider Browser authority would make this more consequential. | Before trusted-site JS/CDP/full-browser authority | Site/network policy is enforced below page JS across navigation, redirects, frames and relevant subresource/network channels; private/link-local/loopback rules are explicit and physically tested. |
| TD-002 | **P1** | ChatGPT app definitions can freeze historical action names **and input schemas** | Existing app instances may keep stale IDs/schemas; inbound aliases cannot repair a call rejected before MCP. | Before stable public schema evolution is relied on | Rebind/versioned migration flow is accepted through ordinary Chat and canonical schemas can evolve without ambiguous stale-client behavior. |
| TD-003 | **P1** | Python/model/OpenAdapt dependency reproduction is not release-grade | Development/qualification can still depend on user/global Python or separately installed artifacts. | Stage 27 distribution hardening | Clean install resolves exact approved artifacts/hashes/versions without developer-machine assumptions; update/rollback is tested. |
| TD-004 | **P2** | Pinned semantic npm graph contains deprecated transitive dependencies | Current graph works but creates maintenance/supply pressure. | Dedicated dependency-maintenance PR before stable release | Graph upgraded/remediated with lock review and full semantic/browser/tunnel acceptance matrix green. |
| TD-005 | **P2** | Runtime-key rotation/repair/uninstall are not complete first-class flows | Lifecycle recovery still contains installer/operator assumptions. | Stage 27 | Rotation, repair and uninstall are explicit idempotent product flows with rollback/error reporting and target-Windows acceptance. |
| TD-006 | **P2** | Browser screenshot -> coordinate action has a narrow TOCTOU gap | Capture and coordinate actuation are separate calls. Freshness reduces but does not eliminate race. | When visual Browser actuation is widened/touched | Action binds strongly enough to current frame/document/target identity that stale visual proposals fail closed; residual race measured/documented. |
| TD-007 | **P2** | Loopback vision endpoint ownership is PID-checked rather than cryptographically authenticated | Same-user process/port races remain weaker than other authenticated boundaries. | Vision/runtime hardening or packaging | Endpoint/session uses authenticated capability/token or equivalent stronger binding with stale/reused-process tests. |
| TD-008 | **P3** | Historical branch refs can look like unfinished work after squash merge or supersession | Ahead/behind graph counts alone can misclassify merged source commits or intentionally retained superseded branches as active development. | Repository-hygiene sweep | Classify refs by associated PR disposition and content before deletion; do not infer unmerged work from graph divergence alone; apply an explicit retention/deletion policy to merged/superseded source branches. |
| TD-009 | **P3** | Repository metadata may still describe the project as `Rust-first` | Metadata does not match the current Python + Node/MJS + PowerShell architecture. | When repository-settings write access is available | Description matches implementation truth; no code rewrite is done merely to satisfy stale metadata. |
| TD-010 | **P2** | Playwright MCP runtime output inherits arbitrary process CWD when output ownership is not explicit | During #118 qualification, `.playwright-mcp` runtime artifacts appeared inside a frozen Git worktree, correctly causing source-provenance revalidation to fail. The accepted run avoided this by launching from an isolated runtime CWD, but ordinary runtime ownership should not depend on caller CWD. | Before/with first Stage 26.3C runtime slice | Browser backend sets an explicit project-owned output directory and/or controlled working directory under platform state/log storage; a regression proves Browser use cannot dirty a source checkout or arbitrary caller directory. |

## TD-001 — Browser network/security boundary

ADR-036 / `BROWSER_HARNESS_ARCHITECTURE.md` owns the future `SiteCapabilityProfile` + Browser Network Gate direction.

```text
trusted destination
  != trusted page instructions
  != local-machine authority
```

Existing `web_open`/`web_interact` verification improves effect correctness but does not close DNS/private-network/subresource policy for broader Browser authority.

## TD-002 — frozen ChatGPT action/schema migration

Historical action aliases only help calls that reach MCP. The physical #111 path demonstrated the stronger stale-schema case: a previously bound ChatGPT app could reject a newly required `expected` field before the MCP server saw the call.

Until a stable migration contract exists, public-schema changes require explicit reconnect/rebind and a fresh ordinary-Chat proof before interpreting later results.

## TD-008 — branch-retention / squash-history ambiguity

Branch hygiene must use PR disposition and actual content, not `ahead/behind` numbers alone.

Two maintenance refs illustrate the distinction:

```text
maintenance/tech-debt-architecture-ci
  source branch of PR #95
  PR #95 = MERGED
  apparent graph-ahead commits are the pre-squash source commits, not unmerged active work

maintenance/slim-live-context-docs
  source branch of PR #96
  PR #96 = CLOSED WITHOUT MERGE as intentionally superseded
  closing record says the branch was retained for history and any useful slimming idea should be re-proposed fresh from current main
```

The useful #96 principle—keep live context concise and move exact evidence into `EVIDENCE_INDEX.md`—has been re-evaluated and ported through the fresh post-26.3B live-context sync rather than merging stale pre-26.3A prose.

Therefore:

- the #95 source ref is a normal merged-PR historical branch candidate for deletion if repository policy does not preserve merged source refs;
- the #96 source ref is intentionally superseded historical material, not current unfinished work; retain or delete it consciously according to branch-retention policy;
- do not mass-delete the repository's historical refs merely because they are old or graph-diverged;
- do not report a branch as containing unmerged work without checking its associated PR/commit disposition.

Close TD-008 when branch-retention policy is explicit and clearly merged/superseded refs are handled consistently.

## TD-010 — Browser runtime output ownership

#118 physical qualification proved fail-closed provenance behavior:

```text
tracked source unchanged
+ untracked .playwright-mcp runtime files appeared in source worktree
-> SOURCE_PROVENANCE_GATE=FAIL
```

That failed run was not acceptance. A fresh run launched from an isolated qualification runtime CWD, kept the source worktree clean through Browser actions and passed the independent frozen Finish Gate.

Permanent runtime hardening should make this isolation intrinsic rather than dependent on how an operator starts the qualification script. The adversarial counterpart is `SRC-003` plus runtime-output ownership meta-tests in `MUTATION_ASSURANCE.md`.

## Documentation/process complexity

The live documentation model deliberately separates:

```text
PROJECT_RISKS.md = ranked project risks
TECH_DEBT.md     = existing technical/process debt
ROADMAP.md       = planned capability sequence
KNOWN_ISSUES.md  = broader limitations/issues
EVIDENCE_INDEX.md = exact accepted evidence navigation
```

Live status/continuation docs should stay concise and point to these owners instead of copying large physical dumps and stale stage lists.

## Explicitly NOT technical debt

The following are unfinished product work or deliberate boundaries, not debt by themselves:

- Stage 26.3C WorkingState, typed recovery/reconciliation and LoopGuard;
- Stage 26.4 candidate skill/demo transfer;
- Stage 26.5 hybrid computer-use integration;
- broad Windows authority not yet accepted;
- arbitrary Python/Local Execution Kernel not yet implemented;
- trusted-site full-browser authority not yet implemented;
- optional Track M multi-chat orchestration;
- optional Track P local planner;
- keeping the public semantic surface small;
- returning `ABSTAIN` on unresolved evidence.

These become technical debt only if the project knowingly ships a temporary compromise and keeps it beyond its intended boundary.

## Maintenance policy

Record a workaround here only if all are true:

1. the workaround exists in current code/config/process;
2. the desired end state is known;
3. leaving it indefinitely increases complexity, security risk, fragility or maintenance cost;
4. there is a concrete close condition.

When closing an item:

```text
implement / simplify
 -> run the owning acceptance matrix
 -> remove compatibility/dead code where applicable
 -> record exact evidence in the appropriate stage/evidence document
 -> remove the open debt entry
```

Historical closure detail belongs in Git history/`EVIDENCE_INDEX.md`, not an ever-growing graveyard.

## Recommended sweep order

Do not stop release-critical work for low-priority cleanup. Current preferred order:

```text
TD-010 before/with first 26.3C Browser/recovery runtime touch
 -> TD-001 alongside any Browser authority widening
 -> TD-002 before relying on stable in-place public schema evolution
 -> establish/execute TD-008 branch-retention policy as a bounded hygiene sweep
 -> TD-003 before stable distribution
 -> batch TD-004/005 with Stage 27 hardening
 -> TD-006/007 when their owning actuation/vision layers are widened
 -> TD-009 whenever repository-settings write access is available
```
