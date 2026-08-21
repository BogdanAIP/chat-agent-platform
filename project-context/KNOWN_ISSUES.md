# Known Issues

Only unresolved issues for the current architecture are listed here. Closed/superseded findings remain at the end for historical clarity.

1. **Present-target browser visual capability remains intentionally limited.** Stage 25 blocks difficult/repeated/tiny classes rather than promoting unsafe clicks.

2. **Browser screenshot -> coordinate action is not atomic.** Freshness is rechecked, but capture and action remain separate calls with a narrow TOCTOU window.

3. **Loopback vision endpoint ownership is PID-checked, not cryptographically authenticated.** A same-user process/port race remains theoretically possible.

4. **Browser network policy is not a complete DNS/redirect sandbox.** DNS rebinding/redirect/private-network isolation remains residual work.

5. **Python/model/OpenAdapt dependency reproducibility is not release-grade.** Stable distribution needs exact artifact/hash/update policy rather than user-global environments.

6. **Pinned semantic npm graph includes deprecated transitive dependencies.** Keep dependency remediation separate from capability architecture changes and rerun the full acceptance matrix.

7. **Generic adaptive Chat-facing actions are not product-accepted.** 1MCP remains internal; generic `tool_schema`/`tool_invoke` is not the ordinary-Chat product contract.

8. **Large exported action surfaces can be truncated in the tested Chat app.** Keep public semantics small/truthful; historical truncation is not a universal numeric limit.

9. **Exported Chat action definitions require explicit Refresh/review.** Do not change public tool schemas casually.

10. **OpenAI product safety may block a composite workflow before MCP invocation.** Distinguish pre-MCP product blocks from local backend failures.

11. **Authorization policy is not accepted for arbitrary Windows consequence classes.** Stage 26.2E proves one harmless isolated real-app text edit, not universal desktop authority.

12. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** Stage 27 remains.

13. **OpenAdapt procedural substrate is target-qualified but not integrated into the normal product path.** Stage 26.3 must integrate ProgramGraph/procedure state through the deterministic Control Plane.

14. **Deterministic local execution Control Plane is architectural direction, not yet accepted product runtime.** TaskState, ProgramGraph progression, checkpoint/recovery/budget state and integrated transition authorization remain to be implemented/tested in Stage 26.3.

15. **First compiled procedure must not silently become product-trusted.** Candidate-first policy remains mandatory even if upstream bootstrap state uses different terminology.

16. **Human demonstration privacy/retention is unresolved.** Long-lived arbitrary desktop capture is not accepted until deletion, encryption and redaction policy is defined/tested.

17. **Private reasoning must never enter task/procedural memory.** Store structured/user-visible goal summaries, observed state, transitions, receipts and verification only.

18. **The 97/97 Stage 26.1E fixture result is not global Windows accuracy.** It proves one controlled role+name path; real apps/custom controls require separate evidence.

19. **`AutomationId` lacks dedicated accepted physical coverage across real applications.** Do not claim broad structural reliability from synthetic tests alone.

20. **One real-application E2E is not broad Windows coverage.** Stage 26.2E physically passed isolated VS Code, but OriginPro/Reaper/custom apps and other control shapes remain separately unqualified.

21. **Arbitrary human “show me once” transfer is not accepted.** Capture/compiler candidates exist; candidate trust, verifier-controlled replay and changed-task reuse remain Stage 26.4 work.

22. **Public desktop/procedure contract is intentionally undecided.** Current five tools remain accepted; use a dedicated ADR rather than overload `web_interact` or add a generic workflow dispatcher.

23. **VS Code is a qualification choice, not an architectural dependency.** Stage 26.2E used isolated VS Code because it offers a medium-complexity real app plus a disposable artifact/profile boundary.

24. **OpenAdapt Desktop is not the qualified runtime baseline.** Packaging ideas may be useful in Stage 27 after version/runtime compatibility review.

25. **Specialized tiny reasoning is not committed to the release path.** TRM/STARM/FPRM or another structured reasoner is optional after real verified procedure-state data and measured need.

26. **Future local general planner is deliberately deferred, not rejected.** Track P is not accepted product functionality. It begins shadow/proposal-only after verified data and measured offline/latency/parallel/deployment need. It may never bypass deterministic authorization/verifier boundaries.

27. **Multi-chat orchestration is a separate parallel layer.** It is not Windows/procedure safety core. Codex/Work remain disabled under the current operating constraint.

28. **No first stable release exists.** Deterministic procedure Control Plane, verified reuse, distribution hardening and clean-user release gates remain incomplete.

29. **Ordinary Chat -> local verified procedure execution without intermediate user command relay is not yet physically accepted.** This is now the first Stage 26.3 end-to-end acceptance target.

30. **Stage 26.3 must not gain autonomy by exposing arbitrary shell/Python execution.** The Control Plane may invoke only typed/scoped capability transitions allowed by the selected ProgramGraph and authorized by current evidence.

31. **Stage 26.2E guarded-input evidence covers one harmless text mutation only.** It is not authority for arbitrary editing, file operations or application commands.

32. **The accepted hidden-focus guard is proven on VS Code/Monaco only.** Other applications with hidden focused accessibility inputs need their own evidence before reusing app-specific identity assumptions.

## Closed / superseded findings

- Stage 25.1/25.2 browser semantic/vision foundations are merged/accepted; historical candidate-runtime rankings no longer define the active path.
- The assumption that Stage 26 must build its own recorder/compiler/skill store from scratch is superseded by exact OpenAdapt Flow/Capture qualification.
- Stage 26.1B bounded Windows Capture passed at `7a9daa9329d81994833c22b4ca2e321927527dcc`.
- Stage 26.1C bounded Windows executor passed at `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`.
- Stage 26.1D isolated desktop-wide UIA traversal as the ~184 s blocker.
- Stage 26.1E replaced desktop-wide resolution with bounded exact-window UIA and passed the controlled scoped suite.
- The old issue that executor/resolver were only qualification assets is closed by 26.2A (#87).
- The old issue that canonical DesktopState did not exist is closed by 26.2B (#88).
- The old issue that native Desktop Grounder did not exist is closed by 26.2C (#89).
- The old issue that deterministic Windows UIA -> vision routing was absent is closed for the bounded controlled-fixture contract by 26.2D (#90).
- The old issue that **no real-application Windows E2E had passed** is closed by Stage 26.2E physical acceptance on exact head `457db0b634f2e47f53d41e359a238840fa3ca2ee`.
- The old issue that the target VS Code focused UIA shape was unknown is closed: accepted evidence shows an exact hidden/zero-size focused `textbox` named by the randomized qualification filename.
- The old same-HWND pre-action focus concern is closed for the accepted VS Code contract by fresh DesktopState fingerprint comparison plus the one-shot window-scoped hidden-focus guard inside the guarded request.
- Stage 26.2E forced CLI cleanup remains forbidden for success; the accepted run exited naturally with code `0`, `FORCED_CLI_CLEANUP=False`, and full rollback.
- The old stacked/unmerged #83/#84/#85 issue is closed; those PRs landed safely.
- The earlier proposal to insert a **local general Agent Planner** immediately after 26.2D is superseded from the current release path. The useful part of that idea has been retained as the **deterministic execution Control Plane** for Stage 26.3, while a true local general planner remains future Track P research rather than being deleted forever.
