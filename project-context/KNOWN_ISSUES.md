# Known Issues

Only unresolved issues for the current architecture are listed here. Closed/superseded qualification findings are kept at the end for historical clarity.

1. **Present-target browser visual capability remains intentionally limited.** Stage 25 baseline is still 3/5 because repeated-row/tiny classes are deliberately blocked rather than promoted unsafely.

2. **Browser screenshot -> coordinate action is not atomic.** Freshness is rechecked before click, but capture and action remain separate calls with a narrow TOCTOU window.

3. **Loopback vision endpoint ownership is PID-checked, not cryptographically authenticated.** A same-user process/port race remains theoretically possible.

4. **Browser network policy is not a complete DNS/redirect sandbox.** Literal private/link-local/metadata targets are blocked while DNS rebinding/redirect/private-network isolation remains residual work.

5. **Python/model/OpenAdapt dependency reproducibility is not release-grade.** Stable distribution needs exact artifact/hash/update policy rather than user-global environments.

6. **Pinned semantic npm graph includes deprecated transitive `glob@10.5.0`.** Keep this as a dedicated dependency follow-up with the full locked acceptance matrix.

7. **Generic adaptive Chat-facing actions are not product-accepted.** 1MCP remains internal; generic `tool_schema`/`tool_invoke` is not the ordinary-Chat product contract.

8. **Large exported action surfaces can be truncated in the tested Chat app.** Keep the public surface small and truthful; historical truncation is not a universal numeric hard limit.

9. **Exported Chat action definitions require explicit Refresh/review.** Do not change the public contract casually during Windows runtime integration.

10. **OpenAI product safety may block a composite workflow before MCP invocation.** Distinguish pre-MCP product blocks from local backend failures.

11. **Authorization policy is not yet accepted for broad Windows desktop consequence classes.** Stage 26.1C proves a bounded harmless executor seam; it does not grant arbitrary desktop authority.

12. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** Stage 27 work remains.

13. **OpenAdapt procedural substrate is target-qualified but not integrated into the product path.** Flow/Capture mechanics are accepted upstream candidates; normal `semantic-projection` does not yet run verified procedures.

14. **First compiled procedure must not silently become product-trusted.** Project policy remains candidate-first even if an upstream bootstrap version is active internally.

15. **Human demonstration privacy/retention is unresolved.** Raw desktop capture may expose visible/typed sensitive data. Long-lived sync/storage is not accepted until deletion, encryption and redaction policy is defined and tested.

16. **Private reasoning must never enter procedural memory.** Store structured/user-visible goals, observed state, transitions, receipts and verification only.

17. **Accepted Windows executor/resolver are still qualification assets, not production runtime.** Stage 26.1C and 26.1E passed on target, but the accepted seams still need extraction into a maintained `runtime/windows` capability boundary with lifecycle/health/logging.

18. **The 97/97 Stage 26.1E fixture result is not global Windows accuracy.** It proves the exercised role+name path on one controlled WinForms fixture. `AutomationId`, custom controls, multiple applications/windows and weaker accessibility providers require separate evidence.

19. **`AutomationId` path is implemented but not physically exercised by the accepted Stage 26.1E benchmark.** Add explicit physical coverage in the Windows accuracy suite before claiming broad structural resolution reliability.

20. **Desktop verifier foundation is not implemented in product runtime.** Executor delivery must not be treated as task completion; before real-application E2E the runtime needs before/after observation and PASS/FAIL/UNKNOWN effect verification.

21. **Canonical `DesktopState` does not yet exist.** Production observation still needs explicit session/application/window identity, coordinate space, freshness/provenance and control fingerprints.

22. **Desktop F16 Grounder is not implemented.** The accepted browser visual path is CSS/Playwright viewport-specific and must not be falsely reused for native Windows pixel coordinates.

23. **Windows semantic/UIA -> vision routing is not accepted.** A separate adversarial suite must cover duplicates, disabled/hidden controls, wrong window/process, overlays, focus changes, stale/recreated windows, structural-path variants and visual ambiguity/ABSTAIN.

24. **No real-application Windows E2E has passed yet.** Qualification fixtures are not sufficient evidence for VS Code, OriginPro, Reaper or arbitrary real applications/custom controls.

25. **Arbitrary human “show me once” transfer is not accepted.** Capture/compiler candidates exist, but candidate trust, verifier-controlled replay and related changed-task reuse still require product evidence.

26. **Public desktop/procedure contract is intentionally undecided.** Current five tools remain accepted. After desktop capability exists, use an ADR; do not overload `web_interact` or add a generic workflow dispatcher.

27. **Concrete future local programs are intentionally not preselected.** Pick the first real application from actual task/evidence and a safe deterministic test artifact.

28. **OpenAdapt Desktop is not the qualified runtime baseline.** Its packaging ideas may be useful in Stage 27, but version/runtime compatibility must be checked against the exact qualified Flow line.

29. **The Stage 26.1C/D/E PR chain is still stacked and unmerged.** #83 is based on `main`, #84 on #83, #85 on #84. Each downstream PR must be retargeted to `main` after its predecessor lands and its resulting diff/CI rechecked; do not blindly merge the stack.

30. **Specialized tiny reasoning is intentionally not committed to the release path.** TRM/STARM/FPRM or another model is only justified after real verified procedure-state data and measured ChatGPT-escalation/latency need exist.

31. **Multi-Chat/Codex orchestration is a separate parallel layer.** It is not part of Windows executor safety or a Stage 27/28 prerequisite.

32. **No first stable release exists.** Windows production runtime, desktop observation/grounder/routing, real-app E2E, verified procedural reuse, distribution hardening and clean-user release gates remain incomplete.

## Closed / superseded findings

- Stage 25.1 and Stage 25.2 browser semantic/vision foundations are merged and accepted; historical candidate-runtime comparisons no longer define the active path.
- The assumption that Stage 26 must build its own recorder/compiler/skill store from scratch is superseded by exact OpenAdapt Flow/Capture qualification.
- **OpenAdapt Capture real bounded Windows qualification is no longer an open issue.** Stage 26.1B passed on target at `7a9daa9329d81994833c22b4ca2e321927527dcc`; evidence is `capture-20260818-194033\result.json`.
- **Windows executor authority qualification is no longer an open issue for the bounded tested seam.** Stage 26.1C exact head `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b` passed loopback/auth/legacy-route/schema/stale-context/fingerprint/focus/input/cleanup gates with zero false/unrelated-window actions. Broad product authorization still remains separate issue #11 above.
- Stage 26.1D measured the ~184 s warm UIA cycle and isolated desktop-wide traversal as the dominant blocker.
- **Desktop-wide UIA traversal is no longer the accepted Windows resolution path.** Stage 26.1E exact head `66390aca1dadf57c4f11568ec311ad6fcdbd7596` passed 97 window-scoped resolutions with zero desktop fallback/binding failures/ambiguities/false actions and reduced action p50/p95 to 3.324/3.720 s (~55x/~50x speedup).
- Earlier Stage 26.1E diagnostic failures (`19d5884...`, `ace6f1eb...`, `1e7f2de...`, `e4cdc43b...`) were qualification discoveries and remained fail-closed with no false/unrelated-window actions; they are not accepted product failures.
