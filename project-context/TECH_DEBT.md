# Technical Debt Register

Status: **CURRENT MAINTENANCE REGISTER**.

This file tracks implementation/process compromises that already exist and should eventually be removed, hardened or simplified.

It is intentionally narrower than `KNOWN_ISSUES.md`, `PROJECT_RISKS.md` and `ROADMAP.md`:

- `TECH_DEBT.md` = existing debt caused by temporary compatibility, incomplete hardening, packaging shortcuts or repository hygiene;
- `KNOWN_ISSUES.md` = broader current limitations/issues, including deliberate product boundaries;
- `PROJECT_RISKS.md` = ranked risks that can affect project success;
- `ROADMAP.md` = planned capability work.

A missing future capability is **not** technical debt merely because it is unfinished.

Always resolve live `main` and active PR heads before acting. This snapshot was refreshed on 2026-08-26 after physical acceptance/merge of PR #107, with docs PR #110 and Browser-interaction PR #111 active.

---

## Priority scale

```text
P0 = reduce on the current critical path because it directly affects safety/correctness
P1 = remove before stable release unless stronger evidence justifies deferral
P2 = important hardening/cleanup; schedule when the owning subsystem is touched
P3 = repository/process hygiene; batch into maintenance sweeps
```

---

# Open debt

| ID | Priority | Debt | Why it is debt | Intended close point | Close condition |
|---|---:|---|---|---|---|
| TD-001 | **P0** | Browser network policy is not a complete DNS/redirect/private-network boundary | Current Browser policy blocks selected unsafe targets but is not a full network sandbox. Wider Browser authority would make this compromise more consequential. | Stage 26.3B/26.5 Browser authority work | Site/network policy is enforced below JS/CDP across navigation, redirects, frames, fetch/XHR, WebSocket-like channels and upload/download destinations; private/link-local/loopback rules are explicit and physically tested. |
| TD-002 | **P1** | Frozen ChatGPT MCP compatibility aliases remain in the launcher | Historical action-name aliases are temporary migration scaffolding needed because existing ChatGPT app definitions can retain stale schemas. They increase compatibility code and test surface. | After stable canonical six-tool rebinding evidence | A newly created/rebound ChatGPT app proves canonical names across read/write/browser/`procedure_run` without legacy aliases; aliases and their dedicated regression anchors are removed. |
| TD-003 | **P1** | Python/model/OpenAdapt dependency reproduction is not release-grade | Current development/qualification can rely on user/global Python or separately installed model/runtime artifacts instead of one exact artifact/hash/update contract. | Stage 27 distribution hardening | Clean install resolves exact approved artifacts, hashes and versions without developer-machine assumptions; update/rollback policy is tested. |
| TD-004 | **P2** | Pinned semantic npm graph contains deprecated transitive dependencies | The graph works today, but deprecated transitives create maintenance/supply pressure and make future runtime upgrades harder. | Dedicated dependency-maintenance PR before stable release | Dependency graph is upgraded/remediated with lockfile review and the full semantic/browser/tunnel acceptance matrix green. |
| TD-005 | **P2** | Runtime-key rotation/repair/uninstall are not complete first-class flows | The runtime works, but lifecycle recovery still contains installer/operator assumptions that should become product operations. | Stage 27 | Rotation, repair and uninstall are explicit idempotent flows with rollback/error reporting and target-Windows acceptance. |
| TD-006 | **P2** | Browser screenshot -> coordinate action has a narrow TOCTOU gap | Screenshot capture and coordinate action are separate calls. Freshness checks reduce risk but cannot make the pair atomic. | When visual Browser actuation is widened/touched | Action is bound to a current frame/document/target identity strongly enough that stale visual proposals fail closed; residual race is measured and documented. |
| TD-007 | **P2** | Loopback vision endpoint ownership is PID-checked rather than cryptographically authenticated | Same-user local process/port races are unlikely but the ownership proof is weaker than the rest of the authenticated execution boundary. | Vision/runtime hardening or packaging | Endpoint/session uses an authenticated capability/token or equivalent stronger binding, with stale/reused-process tests. |
| TD-008 | **P3** | Diverged maintenance branches contain unintegrated unique work | The two maintenance branches remain diverged after #107; they are not safe-to-delete stale pointers because each still carries unique tests/docs/CI changes outside `main`. | Maintenance sweep after #110/#111 settle | Review unique files/commits against current architecture; port only still-valid pieces through a fresh reviewed PR; explicitly reject superseded pieces; then delete both branches. |
| TD-009 | **P3** | Repository metadata still describes the project as `Rust-first` | GitHub repository metadata does not match the current Python + Node/MJS + PowerShell architecture. | As soon as repository-settings write access is available | Repository description matches the current architecture; no code rewrite is done merely to satisfy old metadata. |

---

# Debt currently being reduced by active work

## TD-001 — Browser network/security boundary

ADR-036 / `BROWSER_HARNESS_ARCHITECTURE.md` converts the residual Browser-network weakness into an explicit future `SiteCapabilityProfile` + Browser Network Gate contract.

Important distinction:

```text
trusted destination
  != trusted page instructions
  != local-machine authority
```

A site allowlist may broaden Browser authority only inside its reviewed Browser/network scope. It must never grant Windows/filesystem/Python authority or allow page content to modify the trust list.

PR #107 is now physically accepted and merged: it proves direct `web_open` final-state verification and fail-closed redirect semantics. PR #111 extends ExpectedEffect verification to `web_interact`. Those improve correctness, but neither alone closes TD-001 because DNS resolution, redirects and subresource/network egress still require a lower-level Browser Network Gate before broader JS/CDP authority is accepted.

## TD-008 — maintenance-branch ambiguity

A post-#107 comparison against live `main` on 2026-08-26 confirms both maintenance branches remain diverged and contain unique work:

```text
maintenance/tech-debt-architecture-ci
  ahead 5 / behind 13
  unique diff surface includes:
    .github/workflows/ci.yml
    project-context/EVIDENCE_INDEX.md
    tests/test_ci_maintenance_contract.py

maintenance/slim-live-context-docs
  ahead 6 / behind 12
  unique diff surface includes:
    project-context/ARCHITECTURE.md
    project-context/CURRENT_STATE.md
    tests/test_documentation_consistency.py
    tests/test_live_context_slim_contract.py
```

Some apparent changes overlap work already evolved in `main`, so commit-graph uniqueness is not proof that every old line should be kept. Branch deletion remains blocked until a fresh review decides which unique pieces still fit current architecture.

## Documentation/process complexity

PR #107 merged the simplified documentation-governance model and `PROJECT_RISKS.md`. PR #110 adds this debt register and ADR-036 without restoring the old full-document catalog model.

The ownership split is deliberate:

```text
PROJECT_RISKS.md = ranked project risks
TECH_DEBT.md     = existing technical/process debt
ROADMAP.md       = planned capability sequence
KNOWN_ISSUES.md  = broader limitations/issues
```

---

# Explicitly NOT technical debt

The following are unfinished product work or deliberate boundaries, not debt by themselves:

- remaining Stage 26.3B Browser/Windows verification work;
- Stage 26.3C WorkingState, typed recovery and LoopGuard;
- Stage 26.4 candidate skill/demo transfer;
- Stage 26.5 hybrid computer-use integration;
- broad Windows authority not yet accepted;
- arbitrary Python/Local Execution Kernel not yet implemented;
- Browser Companion/authenticated-browser control not yet implemented;
- optional Track M multi-chat orchestration;
- optional Track P local planner;
- keeping the public semantic surface small;
- returning `ABSTAIN` on unresolved evidence.

These become technical debt only if the project knowingly ships a temporary compromise and then keeps it beyond its intended boundary.

---

# Maintenance policy

Record a workaround here only if all are true:

1. the workaround exists in current code/config/process;
2. the desired end state is known;
3. leaving it indefinitely increases complexity, security risk, fragility or maintenance cost;
4. there is a concrete close condition.

Do not create debt entries for every feature request or research idea.

When closing an item:

```text
implement / simplify
 -> run the owning acceptance matrix
 -> remove compatibility/dead code where applicable
 -> record exact evidence in the appropriate stage/evidence document
 -> remove the entry from Open debt
```

Historical closure detail belongs in Git history/Evidence Index, not an ever-growing graveyard in this file.

---

# Recommended sweep order

Do not stop release-critical work for low-priority cleanup. Current preferred order is:

```text
TD-001 alongside Browser policy/verification work
 -> finish current Stage 26.3B prerequisites
 -> TD-002 when canonical ChatGPT app rebinding can be proved
 -> TD-003 before stable distribution
 -> batch TD-004/005 with Stage 27 hardening
 -> TD-006/007 when their owning actuation/vision layers are widened
 -> review/resolve TD-008 after #110/#111 settle
 -> close TD-009 whenever repository-settings write access is available
```

This keeps debt repayment tied to the subsystem that can actually close it instead of creating a large unrelated cleanup detour.
