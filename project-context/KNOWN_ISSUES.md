# Known Issues

Status: **CURRENT LIMITATION REGISTER**.

This file lists unresolved limitations in the current architecture/product. It is not the ranked risk register (`PROJECT_RISKS.md`), release plan (`ROADMAP.md`) or technical-debt owner (`TECH_DEBT.md`).

Resolve live repository state before acting. Active PR/design detail belongs in `CURRENT_STATE.md`.

## Current unresolved issues

1. **Broad real-application computer-use reliability is not yet proven.** Representative Browser and Windows/application L3 verticals are accepted, but native Win32, Electron, Office-style apps, file/dialog flows and environment variants still need broader characterization.

2. **Stage 26.3C production recovery integration is incomplete.** WorkingState/typed reconciliation/budgets/LoopGuard L1 foundation is accepted through #124, but consequence-bearing procedures/capabilities still need restart-safe integration and physical qualification.

3. **Machine/power-loss transactional durability is not an accepted WorkingState/procedure guarantee.** Current Stage 26.3C production research deliberately scopes concrete guarantees; missing/corrupt/inconsistent durable state must fail closed rather than imply a database-grade WAL guarantee that has not been accepted.

4. **Browser runtime output ownership is not fully intrinsic.** #118 caught Playwright runtime artifacts entering a source worktree when process CWD was inherited. The accepted gate isolated runtime CWD; normal runtime still needs an explicit project-owned output/state directory. See TD-010.

5. **Browser screenshot -> coordinate actuation is non-atomic.** Freshness/identity guards reduce risk, but capture and coordinate action remain separate calls with a narrow TOCTOU window.

6. **Browser network policy is not a complete DNS/redirect/private-network sandbox.** Current Browser authority is intentionally narrower than future trusted-site JS/CDP/full-browser authority.

7. **Loopback vision endpoint ownership is PID-checked rather than cryptographically authenticated.** A same-user process/port race remains weaker than a token/capability-bound endpoint.

8. **Python/model/OpenAdapt dependency reproduction is not release-grade.** Stable distribution still needs exact artifact/hash/update/rollback handling independent of developer/global environments.

9. **Pinned semantic npm dependencies include deprecated transitive packages.** Upgrade only through a dedicated reviewed lock/dependency change with the relevant semantic/browser/tunnel acceptance matrix.

10. **ChatGPT app definitions can retain frozen historical action IDs/input schemas.** A launcher alias can repair only calls that reach MCP; it cannot update a client snapshot that rejects a call before transport. Explicit rebind/reconnect remains necessary for material public-schema evolution. See `SEMANTIC_FROZEN_ACTION_COMPATIBILITY.md`.

11. **Compatibility aliases remain migration debt.** Historical inbound semantic action aliases should be removed only after canonical six-tool calls are proven stable across fresh/rebound app instances.

12. **Arbitrary Windows/local execution authority is not accepted.** Existing Windows foundations and representative app evidence do not grant generic desktop, shell, Python or raw UIA/backend dispatch authority.

13. **OpenAdapt broader production integration is not accepted.** Flow/Capture are qualified and selected for specific procedure/compiler/resume/effect-evidence roles, but fresh Stage Research must validate each production consumer against `ARCHITECTURE_REUSE_BASELINE.md`. Upstream completion/effect verdicts never become unconditional project PASS/DONE.

14. **Human demonstration privacy/retention and trusted promotion remain unresolved.** Long-lived arbitrary desktop capture requires deletion/redaction/encryption/retention rules. One demonstration creates at most a candidate skill; promotion needs independent replay/regression/variant evidence.

15. **No stable end-user release exists.** Remaining critical work includes Stage 26.3C production integration, broad physical coverage, 26.4/26.5 integration, distribution hardening and clean-user E2E.

## Current public-surface boundary

The normal Chat-facing surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Generic adaptive `tool_schema` / `tool_invoke`, raw backend catalogs and arbitrary dispatch remain unaccepted. Six is the current accepted contract, not an eternal maximum; any new consequence class requires a truthful reviewed contract/acceptance decision.

## Current evidence-scope cautions

Do not overclaim from scoped evidence:

- Stage 26.1E controlled UIA results are not global Windows accuracy;
- Stage 26.2E one VS Code task is not broad application coverage;
- accepted Browser L3 uses headless Playwright/Chrome on target Windows and does not prove control of an already-open visible desktop Chrome session;
- `AutomationId`/custom controls/application-specific semantics still need representative real-app evidence where relied upon;
- physical acceptance of one procedure does not make arbitrary procedures trusted.

## Closed / superseded findings

These are no longer open issues:

- Stage 25.1/25.2 semantic/vision Browser foundations are accepted for recorded scope.
- The assumption that Stage 26 must build its recorder/compiler/procedural substrate from scratch is superseded by OpenAdapt qualification and the explicit reuse strategy.
- Stage 26.1B-E and 26.2A-E established the current bounded Windows foundation and representative VS Code E2E.
- Transport Supervisor v1 is accepted/merged; normal direct semantic bootstrap does not require 1MCP.
- Stage 26.3A canonical six-tool `procedure_run` is physically accepted, including zero-overwrite abstention for the registered workspace-artifact procedure.
- Stage 26.3B shared Verification Kernel + independent Finish Gate is **accepted/closed for recorded representative scope** across file, Browser and Windows/application evidence; it is no longer an unfinished issue.
- Browser #118 closed the remaining recorded 26.3B source/install/dependency provenance repeat while rejecting invalid earlier attempts.
- Stage 26.3C WorkingState/typed reconciliation/budget/LoopGuard/StagnationReport **L1 foundation is accepted/merged through #124**. The remaining issue is production/cross-capability integration, not absence of the model itself.
- The old pre-#127 assumption that a PR-body design update alone could justify a new persistence/recovery primitive is superseded by the current `stage-research` re-entry/mechanism-depth gate.

Historical exact SHAs and detailed closure evidence belong in `EVIDENCE_INDEX.md`, Stage records and Git history rather than this current limitation list.
