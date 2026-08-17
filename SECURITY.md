# Security Policy

Security fixes target the current `main` branch until a versioned release policy is published.

## Reporting

Do not publish tokens, API keys, private endpoints, exploit payloads or sensitive logs in public issues/PRs. Prefer GitHub private vulnerability reporting when available; otherwise request a private channel without including exploit details.

## Current normal security boundary

The accepted normal semantic path is outbound from the user's machine:

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> scoped Filesystem / isolated Playwright / focused local adapters
```

The normal semantic path does **not** require a local port-3050 1MCP hop. Port 3050/1MCP remains relevant only to accepted legacy/diagnostic/adaptive profiles.

The project does not implement its own public ingress, relay, tunnel, credential vault or generic authorization server.

## Secrets

Secrets, including the OpenAI tunnel runtime key, must never be committed. The tunnel runtime key should have only the permissions required by tunnel operation and is stored locally through Windows DPAPI `CurrentUser` by the manager.

The direct controller temporarily provides `CONTROL_PLANE_API_KEY` to tunnel-client startup. Stage 25.1 security work must explicitly verify that semantic-projection and downstream child backends do not inherit that credential unless required; do not rely on an undocumented assumption.

## Capability scope

The shipped/reference and diagnostic profiles remain intentionally scoped. The normal semantic projection exposes only reviewed semantic operations and must not leak generic/raw backend capabilities.

Raw Playwright code/evaluate/file-upload/direct-network-request actions are not part of the accepted semantic surface. Filesystem roots remain explicit and path traversal/absolute-path escape is rejected by the projection.

Stage 25.1 must additionally test Windows symlink/junction containment because lexical path validation alone is not sufficient evidence of real filesystem root containment.

## Browser network boundary

The isolated Playwright profile is a browser/process isolation configuration, not a guaranteed network sandbox. `web_open` accepts reviewed HTTP/HTTPS navigation. Before broad visual auto-interaction is accepted, the project must explicitly test/define behavior for localhost and private-network destinations rather than assuming they are unreachable.

## Local vision boundary

Accepted Stage 25 grounding uses an already-running local llama.cpp loopback endpoint and reviewed local image data. Ordinary Chat must not receive arbitrary model administration, raw prompts, arbitrary inference endpoints or unrestricted remote image URLs.

The visual model never performs a browser action. It may only return bounded perception evidence that a deterministic adapter can resolve or reject.

Stage 25.1 automatic visual interaction must satisfy:

```text
same Playwright page/session
  -> capture current state
  -> local visual grounding
  -> deterministic validation + freshness proof
  -> action in same page/session OR ABSTAIN
```

If page identity, viewport/scroll/scale state, coordinate mapping or freshness is uncertain, the result must be ABSTAIN and the page must remain unchanged. Never implement a blind cross-session `VLM coordinate -> click` path.

## Resource/process boundary

The F16 vision model is heavyweight relative to the target laptop. It must not be loaded permanently by default. A focused non-agentic lifecycle owner should enforce approved artifact identity, memory admission, health, cleanup and idle unload. Do not turn the semantic projection or public manager into a general AI/process orchestration platform.

## Supply-chain status

- complete reachable Git history is scanned with checksum-pinned Gitleaks;
- GitHub Actions are SHA-pinned where configured;
- CodeQL currently analyzes GitHub Actions, not the full active Node/Python codebase;
- semantic projection uses exact top-level npm versions but stable distribution still needs a locked/reproducible transitive dependency graph;
- Stage 25 Python dependency management is intentionally small but also needs a reproducible update policy before stable release.

These are active hardening tasks, not evidence that the current branch is unsafe by default.

## Historical infrastructure

Historical Yandex/Tailscale/custom universal-core paths are fallback/history only and must not be treated as current authorization boundaries.
