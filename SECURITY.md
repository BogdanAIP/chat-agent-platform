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
  -> direct stdio semantic-projection launcher
  -> semantic-projection core
  -> scoped Filesystem / isolated Playwright / focused local adapters
```

The normal semantic path does **not** require a local port-3050 1MCP hop. Port 3050/1MCP remains accepted legacy/diagnostic/adaptive infrastructure.

The project does not implement its own public ingress, relay, tunnel, credential vault or generic authorization server.

## Secrets and child-process environment

Secrets, including the OpenAI tunnel runtime key, must never be committed. The tunnel runtime key should have only permissions required by tunnel operation and is stored locally through Windows DPAPI `CurrentUser` by the manager.

Review of exact `openai/tunnel-client v0.0.11` established that its stdio MCP child is launched with inherited parent environment. Therefore `CONTROL_PLANE_API_KEY` would reach semantic-projection if the project did nothing.

The accepted boundary is now explicit:

```text
tunnel-client inherited environment
  -> semantic-projection-launcher.mjs
       -> delete CONTROL_PLANE_API_KEY
       -> delete OPENAI_API_KEY
       -> import semantic-projection core
```

A Windows sentinel regression proves scrub occurs before core import and does not echo the injected value. Downstream Filesystem/Playwright are then launched through the pinned MCP SDK stdio transport, which applies its own restricted environment behavior.

Do not remove the secure launcher merely because a future upstream version appears to filter environment; first prove and review that new contract.

## Capability scope

The normal semantic projection exposes only reviewed semantic operations and must not leak generic/raw backend capabilities.

Raw Playwright code/evaluate/file-upload/direct-network-request actions are not part of the accepted semantic surface. Filesystem roots remain explicit; lexical traversal/absolute-path escape is rejected by projection; real Windows junction read/write escape attempts are also regression-tested and blocked by the current stack.

## Browser network boundary

The isolated Playwright profile is browser/process isolation, not a complete network sandbox.

`web_open` accepts HTTP/HTTPS but now applies a direct-destination policy before `browser_navigate`:

- reviewed loopback remains allowed: `localhost`, `*.localhost`, IPv4 127/8 and IPv6 `::1`;
- direct RFC1918, CGNAT, link-local/metadata and other explicit non-public/special IP destinations are rejected by default;
- direct `metadata.google.internal` is rejected;
- Playwright `blocked-origins` additionally covers reviewed metadata endpoints as defense-in-depth.

Do **not** treat Playwright `allowed-origins`/`blocked-origins` as the primary security boundary. The pinned upstream documentation explicitly states that origin filtering is not a security boundary and does not affect redirects. DNS hostname resolution/rebinding and redirects are therefore residual risks if future workflows require a stronger private-network/metadata isolation guarantee.

Broader private-LAN browser access should be a separately reviewed capability/policy rather than silently weakening the normal web scope.

## Local vision boundary

Accepted Stage 25 grounding uses reviewed local image data and a loopback llama.cpp endpoint. Ordinary Chat must not receive arbitrary model administration, raw model prompts, arbitrary inference endpoints or unrestricted remote image URLs.

The visual model never performs a browser action. Production layers are separated:

```text
focused runtime owner
  -> reviewed loopback inference
  -> production visual grounder
  -> deterministic class-aware authorization
  -> same-session freshness bridge
  -> action OR ABSTAIN
```

The production grounder does not own runtime, browser state or action. Repeated-row and tiny classes remain non-authorizing until separately promoted by measured evidence.

The runtime-backed grounder requires the controller's exact owned PID and, before sending screenshot bytes, verifies with Windows `Get-NetTCPConnection` that the reviewed `127.0.0.1:3068` listener is owned by that PID. A mismatch fails closed and attempts cleanup of only the ownership-verified runtime. This closes the stale-state case where an owned process remains alive while a different local process already owns the inference port.

This PID/listener check is not cryptographic endpoint authentication. Loopback TCP cannot eliminate a theoretical local race in which the verified llama.cpp listener disappears after the check and another local process immediately acquires the same port before the request connects. The current boundary therefore assumes no actively malicious same-user local process racing the inference socket. A stronger future threat model would require an authenticated per-instance endpoint, stronger OS isolation or another transport that can bind peer identity to the request.

Automatic visual interaction requires capture/action in the same Playwright session and fresh CSS-pixel evidence. Layout, scroll, overlay and navigation changes observed before commit are fail-closed through an exact viewport screenshot hash. Prepared targets are one-shot, TTL-bounded and capacity-bounded.

The final freshness screenshot and `browser_mouse_click_xy` are nevertheless two separate MCP calls. A page can theoretically mutate in the small interval after the final screenshot response and before the coordinate click is processed. This residual screenshot-to-click TOCTOU window is why automatic semantic-miss -> vision escalation is not part of Stage 25.1, and why consequential visual actions need additional application-specific safeguards or a more atomic backend primitive before promotion. Never implement a blind cross-session `VLM coordinate -> click` path.

## Resource/process boundary

The F16 vision model is heavyweight relative to the target laptop and is not an always-on default service. The focused lifecycle owner enforces approved artifact/runtime identity, conservative memory admission, loopback health, exact process ownership, Touch, TTL/resource-pressure unload and explicit cleanup.

It must not become a generic model runner or kill Chrome/unrelated processes.

## Supply-chain status

- complete reachable Git history is scanned with checksum-pinned Gitleaks;
- GitHub Actions are SHA-pinned where configured;
- CodeQL analyzes Actions, JavaScript/TypeScript and Python;
- Dependabot covers Actions, semantic npm and Python requirements;
- semantic projection uses exact top-level npm pins plus a committed lockfile;
- product and acceptance semantic installs use `npm ci --ignore-scripts --no-audit --no-fund` and refuse unlocked install when dependencies are absent;
- standalone installed-layout acceptance also carries the lockfile and secure launcher;
- current vision Python dependency surface is small and exactly pins `Pillow==12.3.0`, but stable distribution still needs an explicit Python artifact/hash/update policy;
- downloaded tunnel/model/runtime artifacts retain checksum/hash/version verification where applicable.

## Historical infrastructure

Historical Yandex/Tailscale/custom universal-core and LM Studio/llmster paths are fallback/history only and must not be treated as current authorization boundaries.
