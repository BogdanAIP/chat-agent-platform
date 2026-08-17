# Security Policy

Security fixes target the current `main` branch until a versioned release policy is published.

## Reporting

Do not publish tokens, API keys, private endpoints, exploit payloads or sensitive logs in public issues/PRs. Prefer GitHub private vulnerability reporting when available; otherwise request a private channel without including exploit details.

## Current normal security boundary

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> scoped Filesystem / isolated Playwright / focused local adapters
```

The normal semantic path does not require a local port-3050 1MCP hop. Port 3050/1MCP remains relevant only to accepted legacy/diagnostic/adaptive profiles.

The project does not implement its own public ingress, relay, tunnel, credential vault or generic authorization server.

## Secrets

Secrets, including the OpenAI tunnel runtime key, must never be committed. The tunnel runtime key should have only the permissions required by tunnel operation and is stored locally through Windows DPAPI `CurrentUser` by the manager.

The direct controller temporarily provides `CONTROL_PLANE_API_KEY` to tunnel-client startup. Explicit child-environment inheritance testing remains pending. Do not assume semantic-projection or downstream Filesystem/Playwright children cannot see the key until a regression proves that boundary; scrub downstream environments if the test shows inheritance.

## Filesystem scope

Filesystem roots remain explicit. Lexical absolute/parent traversal is rejected by the semantic projection.

Stage 25.1 additionally proved the current pinned Windows stack against a real directory junction:

```text
allowed workspace/outside-link -> junction -> outside directory
```

Normal semantic calls produced:

```text
workspace_read through junction = blocked
workspace_write through junction = blocked
normal write inside root = works
```

The suspected junction escape did not reproduce. Keep this regression because downstream Filesystem dependency behavior may change.

## Browser scope

Raw Playwright code/evaluate/file-upload/direct-network-request actions are not part of the accepted semantic surface.

The isolated Playwright profile is a browser/process isolation configuration, not a guaranteed network sandbox. `web_open` intentionally supports reviewed HTTP/HTTPS navigation and accepted tests/workflows use localhost. Therefore localhost/private-network behavior must be documented and regression-tested rather than hidden behind an arbitrary blanket block.

Vision fallback must not autonomously expand navigation scope from on-screen content. Its accepted role is grounding/action within the current already-authorized Playwright page/session.

## Same-session local vision boundary

The visual model never performs a browser action. It may only return bounded perception evidence that a deterministic adapter can resolve or reject.

Stage 25.1 now proves this internal action boundary in Windows CI:

```text
same Playwright client/session
  -> CSS screenshot
  -> bounded grounding result
  -> one-shot prepared target
  -> fresh CSS screenshot
  -> exact dimensions + screenshot SHA256
  -> coordinate action OR ABSTAIN
```

Proved stale/uncertain no-action cases include layout shift, scroll, overlay, navigation/page replacement, replayed token, missing target and ambiguous target. Existing exact five-tool semantic acceptance remains green.

The freshness policy is deliberately strict. Do not weaken it merely to increase hit rate.

## Local vision runtime/process boundary

A focused non-agentic lifecycle owner now exists for the reviewed F16 profile. Synthetic Windows acceptance proves:

- exact runtime version markers;
- exact model/mmproj size + SHA256;
- loopback-only binding;
- physical + virtual memory admission;
- process ownership using PID + exact executable + full command-line SHA256 + UTC creation ticks;
- idempotent Start;
- Touch + idle TTL unload;
- explicit Stop;
- model tamper rejection;
- foreign-listener fail-closed behavior;
- ownership-mismatch fail-closed behavior.

The controller does not kill Chrome or arbitrary user processes. **Real target-laptop F16 lifecycle acceptance is still required before product promotion.**

## Production grounding authorization

Benchmark output is not automatically actionable. Stage 25.1 adds a stricter class-aware promotion layer:

- text/state targets require unique target-blind inventory and unique refinement;
- icon targets require unique two-pass grounding and positive overlap;
- repeated-row and tiny targets remain forced ABSTAIN until separate target evidence promotes them;
- absent/unreviewed/ambiguous/error paths do not authorize action.

Do not replace this with one global IoU threshold; accepted text evidence includes very low coarse/refined overlap.

## Supply-chain status

- complete reachable Git history is scanned with checksum-pinned Gitleaks;
- GitHub Actions remain SHA-pinned where configured;
- CodeQL now analyzes Actions, JavaScript/TypeScript and Python; all three jobs passed on the current Stage 25.1 evidence head;
- Dependabot now monitors Actions, semantic npm and root pip dependencies;
- semantic projection still lacks a committed npm lockfile and currently installs with `--package-lock=false`;
- Stage 25 Python dependency management remains small but needs a stable reproducibility/update policy before release.

Dependency monitoring is improved; reproducible installation is still pending.

## Historical infrastructure

Historical Yandex/Tailscale/custom universal-core paths are fallback/history only and must not be treated as current authorization boundaries.
