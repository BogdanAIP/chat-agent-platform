# Technical Debt Register

Status: **CURRENT MAINTENANCE REGISTER**.

This file tracks implementation/process compromises that already exist and should eventually be removed, hardened or simplified.

It is intentionally narrower than `KNOWN_ISSUES.md`, `PROJECT_RISKS.md` and `ROADMAP.md`:

- `TECH_DEBT.md` = existing debt caused by temporary compatibility, incomplete hardening, packaging shortcuts or repository hygiene;
- `KNOWN_ISSUES.md` = all current limitations/issues, including deliberate product boundaries;
- `PROJECT_RISKS.md` = ranked risks that can affect project success;
- `ROADMAP.md` = planned capability work.

A missing future capability is **not** technical debt merely because it is unfinished.

Always resolve live `main` and active PR heads before acting. The snapshot below was reviewed on 2026-08-26 against live `main` plus active PR #107/#108 state.

---

## Priority scale

```text
P0 = should be reduced on the current critical path because it directly affects safety/correctness
P1 = remove before stable release unless stronger evidence justifies deferral
P2 = important hardening/cleanup; schedule when the owning subsystem is touched
P3 = repository/process hygiene; batch into maintenance sweeps
```

---

# Open debt

| ID | Priority | Debt | Why it is debt | Intended close point | Close condition |
|---|---:|---|---|---|---|
| TD-001 | **P0** | Browser network policy is not a complete DNS/redirect/private-network boundary | Current browser policy blocks selected unsafe targets but is not a full network sandbox. Broader Browser Harness-style authority would make this compromise more consequential. | Stage 26.3B/26.5 browser authority work | Site/network policy is enforced below JS/CDP across navigation, redirects, frames, fetch/XHR, WebSocket-like channels and upload/download destinations; private/link-local/loopback rules are explicit and physically tested. |
| TD-002 | **P1** | Frozen ChatGPT MCP compatibility aliases remain in the launcher | Historical action-name aliases are temporary migration scaffolding needed because existing ChatGPT app definitions can retain stale schemas. They increase compatibility code and test surface. | After stable canonical six-tool rebinding evidence | A newly created/rebound ChatGPT app proves canonical names across read/write/browser/`procedure_run` without legacy aliases; aliases and their dedicated regression anchors are removed. |
| TD-003 | **P1** | Python/model/OpenAdapt dependency reproduction is not release-grade | Current development/qualification can rely on user/global Python or separately installed model/runtime artifacts instead of one exact artifact/hash/update contract. | Stage 27 distribution hardening | Clean install resolves exact approved artifacts, hashes and versions without developer-machine assumptions; update/rollback policy is tested. |
| TD-004 | **P2** | Pinned semantic npm graph contains deprecated transitive dependencies | The graph works today, but deprecated transitives create maintenance/supply pressure and make future runtime upgrades harder. | Dedicated dependency-maintenance PR before stable release | Dependency graph is upgraded/remediated with lockfile review and the full semantic/browser/tunnel acceptance matrix green. |
| TD-005 | **P2** | Runtime-key rotation/repair/uninstall are not complete first-class flows | The runtime works, but lifecycle recovery still contains installer/operator assumptions that should become product operations. | Stage 27 | Rotation, repair and uninstall are explicit idempotent flows with rollback/error reporting and target-Windows acceptance. |
| TD-006 | **P2** | Browser screenshot -> coordinate action has a narrow TOCTOU gap | Screenshot capture and coordinate action are separate calls. Freshness checks reduce risk but cannot make the pair atomic. | When visual browser actuation is widened/touched | Action is bound to a current frame/document/target identity strongly enough that stale visual proposals fail closed; residual race is measured and documented. |
| TD-007 | **P2** | Loopback vision endpoint ownership is PID-checked rather than cryptographically authenticated | Same-user local process/port races are unlikely but the ownership proof is weaker than the rest of the authenticated execution boundary. | Vision/runtime hardening or packaging | Endpoint/session uses an authenticated capability/token or equivalent stronger binding, with stale/reused-process tests. |
| TD-008 | **P3** | Diverged maintenance branches contain unintegrated unique work | `maintenance/tech-debt-architecture-ci` is 5 commits ahead / 12 behind `main`; `maintenance/slim-live-context-docs` is 6 ahead / 11 behind. They are not safe-to-delete stale pointers: unique CI/evidence/document-slimming tests and docs remain outside `main`, while overlapping files have also evolved independently. This creates repository-state ambiguity and future merge risk. | Maintenance sweep after #107/#108 settle | Review unique files/commits against current architecture; port only still-valid pieces through a fresh reviewed PR; explicitly reject superseded pieces; then delete both maintenance branches. |
| TD-009 | **P3** | Repository metadata still describes the project as `Rust-first` | GitHub currently says `Chat-centric open-source agent platform: Rust-first local execution core`, while the runtime is primarily Python + Node/MJS + PowerShell and GitHub reports Python as the repository language. This is confirmed current metadata drift, not a hypothetical mismatch. | As soon as repository-settings write access is available | GitHub repository description matches the current architecture; no code rewrite is done merely to satisfy old metadata. |

---

# Debt currently being reduced by active work

## TD-001 — Browser network/security boundary

ADR-036 / `BROWSER_HARNESS_ARCHITECTURE.md` converts the existing residual browser-network weakness into an explicit future `SiteCapabilityProfile` + Browser Network Gate contract.

Important distinction:

```text
trusted destination
  != trusted page instructions
  != local-machine authority
```

A site allowlist may broaden browser authority only inside its reviewed browser/network scope. It must never grant Windows/filesystem/Python authority or allow page content to modify the trust list.

PR #107 is already tightening Browser verification for navigation final state. That is complementary correctness work, but redirect/network trust widening remains separate and must not be inferred from navigation verification alone.

## TD-008 — maintenance-branch ambiguity

A 2026-08-26 comparison against live `main` proved both maintenance branches are diverged and still contain unique work:

```text
maintenance/tech-debt-architecture-ci
  ahead 5 / behind 12
  unique-looking surface includes:
    .github/workflows/ci.yml
    project-context/EVIDENCE_INDEX.md
    tests/test_ci_maintenance_contract.py

maintenance/slim-live-context-docs
  ahead 6 / behind 11
  unique-looking surface includes:
    project-context/ARCHITECTURE.md changes
    tests/test_live_context_slim_contract.py
```

PR #107 overlaps some documentation-consistency/current-state work but does not contain all of those files. Therefore branch deletion is explicitly blocked until a fresh review decides which unique pieces remain valid.

## Documentation/process complexity

Active PR #107 introduces `PROJECT_RISKS.md` and simplifies documentation-governance ownership. If merged, that reduces the current documentation/status-drift risk. It should not create a second competing technical-debt ranking: this file owns debt inventory; `PROJECT_RISKS.md` owns project-risk ranking.

---

# Explicitly NOT technical debt

The following are unfinished product work or deliberate boundaries, not debt by themselves:

- Stage 26.3B Browser/Windows verification adapters still being implemented;
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

When introducing a temporary workaround, record it here only if all are true:

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
 -> review/resolve TD-008 after #107/#108 settle
 -> close TD-009 whenever repository-settings write access is available
```

This keeps debt repayment tied to the subsystem that can actually close it instead of creating a large unrelated cleanup detour.
