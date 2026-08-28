# Technical Debt Register

Status: **CURRENT MAINTENANCE REGISTER**.

This file tracks compromises that **already exist** and should later be removed, hardened or simplified.

It is narrower than:

- `KNOWN_ISSUES.md` = unresolved limitations/issues;
- `PROJECT_RISKS.md` = ranked risks to project success;
- `ROADMAP.md` = planned capability work.

A missing future capability is not technical debt merely because it is unfinished.

## Priority scale

```text
P0 = current safety/correctness critical path
P1 = remove before stable release unless stronger evidence justifies deferral
P2 = important hardening/cleanup; schedule when owning subsystem is touched
P3 = repository/process hygiene; batch into maintenance sweeps
```

## Open debt

| ID | Priority | Debt | Why it is debt | Close condition |
|---|---:|---|---|---|
| TD-001 | **P0** | Browser network policy is not a complete DNS/redirect/private-network boundary | Current Browser policy is intentionally narrower than future trusted-site JS/CDP/full-browser authority | Site/network policy is enforced below page JS across navigation/redirect/frame/relevant network channels; private/link-local/loopback policy is explicit and physically tested before wider authority. |
| TD-002 | **P1** | ChatGPT app definitions can freeze historical action names/input schemas | Existing app instances may reject changed schemas before MCP can apply aliases | A reviewed rebind/versioned migration flow is accepted through ordinary Chat so public schemas can evolve without ambiguous stale-client behavior. |
| TD-003 | **P1** | Python/model/OpenAdapt dependency reproduction is not release-grade | Development/qualification can still depend on user/global Python or separately installed artifacts | Stage 27 clean install resolves exact approved artifacts/hashes/versions without developer-machine assumptions and update/rollback is tested. |
| TD-004 | **P2** | Pinned semantic npm graph contains deprecated transitive dependencies | Creates maintenance/supply pressure | Upgrade/remediate in a dedicated lock review with full semantic/browser/tunnel acceptance green. |
| TD-005 | **P2** | Runtime-key rotation/repair/uninstall are not complete first-class flows | Lifecycle recovery still includes installer/operator assumptions | Rotation, repair and uninstall become explicit idempotent product flows with rollback/error reporting and target-Windows acceptance. |
| TD-006 | **P2** | Browser screenshot -> coordinate action has a narrow TOCTOU gap | Capture and coordinate actuation are separate calls | Bind visual proposals strongly enough to current frame/document/target identity that stale proposals fail closed; document/measure residual race. |
| TD-007 | **P2** | Loopback vision endpoint ownership is PID-checked rather than cryptographically authenticated | Same-user process/port races remain weaker than stronger authenticated boundaries | Use authenticated capability/token or equivalent stronger binding with stale/reused-process tests. |
| TD-008 | **P3** | Historical branch refs can look like unfinished work after squash merge/supersession | ahead/behind counts alone can misclassify historical source branches | Establish explicit branch retention policy and classify refs by associated PR disposition/content before deletion. |
| TD-009 | **P3** | Repository metadata may still describe project as `Rust-first` | Metadata does not match current Python + Node/MJS + PowerShell architecture | Update repository description when settings write access is available; do not rewrite code merely to fit metadata. |
| TD-010 | **P2** | Playwright runtime output can inherit arbitrary caller CWD when output ownership is not explicit | #118 qualification observed `.playwright-mcp` artifacts inside a frozen source worktree, correctly failing provenance | Browser backend owns explicit output/working directories under platform state/log roots; regression proves Browser use cannot dirty source checkout/arbitrary caller directory. |

## Important detail — TD-010

#118 proved the provenance gate was fail-closed:

```text
tracked source unchanged
+ untracked runtime files appear in source worktree
-> source provenance revalidation FAIL
```

That failed attempt was not acceptance. The accepted run used an isolated runtime CWD.

Permanent hardening should make this isolation intrinsic rather than operator-dependent. It may land with the next relevant Browser/runtime/recovery touch; it is not evidence that the already-merged Stage 26.3C L1 state foundation is incomplete.

## Branch-hygiene caution — TD-008

Do not infer unfinished work from graph divergence alone. Squash-merged source branches can remain graph-ahead of `main`, and intentionally superseded branches may be retained for history.

Branch cleanup must inspect associated PR disposition and actual content before deletion.

## Documentation/process ownership

```text
PROJECT_RISKS.md   = ranked project risk
TECH_DEBT.md       = existing compromise/maintenance debt
KNOWN_ISSUES.md    = unresolved limitations
ROADMAP.md         = planned capability/release sequence
EVIDENCE_INDEX.md  = exact accepted physical evidence navigation
```

Live status/continuation documents should point to these owners rather than copy their details.

## Explicitly NOT technical debt

The following are unfinished product work or deliberate boundaries, not debt by themselves:

- remaining Stage 26.3C production WorkingState/restart-reconciliation/cross-capability integration after the accepted #124 L1 foundation;
- Stage 26.4 candidate skill/demo transfer;
- Stage 26.5 hybrid computer-use integration;
- broad Windows authority not yet accepted;
- arbitrary Python/Local Execution Kernel not yet implemented;
- trusted-site full-browser authority not yet implemented;
- optional Track M multi-chat orchestration;
- optional Track P local planner;
- keeping the public semantic surface small;
- returning `ABSTAIN` on unresolved evidence.

These become debt only if the project knowingly ships a temporary compromise beyond its intended boundary.

## Maintenance policy

Record a workaround here only if all are true:

1. the workaround exists in current code/config/process;
2. the desired end state is known;
3. leaving it indefinitely increases complexity, security risk, fragility or maintenance cost;
4. there is a concrete close condition.

When closing debt:

```text
implement / simplify
 -> run owning acceptance matrix
 -> remove compatibility/dead code where applicable
 -> record exact accepted evidence in its owner
 -> remove the open debt entry
```

Historical closure detail belongs in Git history/`EVIDENCE_INDEX.md`, not an ever-growing graveyard.

## Recommended sweep order

Do not stop release-critical work for low-priority cleanup.

```text
TD-010 with the next relevant Browser/runtime/recovery touch
 -> TD-001 before any Browser authority widening
 -> TD-002 before relying on stable in-place public schema evolution
 -> bounded TD-008 branch-retention sweep
 -> TD-003 before stable distribution
 -> TD-004/005 with Stage 27 hardening
 -> TD-006/007 when their owning layers are widened
 -> TD-009 whenever repository-settings write access is available
```
