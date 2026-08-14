# Security Policy — Bridge

## Trust boundaries

Normal path:

```text
ChatGPT -> OpenAI tunnel service -> official tunnel-client -> loopback 1MCP/focused adapter -> selected backend(s)
```

The tunnel provides authenticated reachability. It is not a substitute for backend-level scope, truthful tool semantics or product-level safety review.

## Security objective

Security should control consequence, scope and lifetime without making legitimate workflows impossible.

Use three states:

- **AVAILABLE:** backend is registered/approved locally;
- **ACTIVE:** backend process is running for the current task;
- **AUTHORIZED:** the requested action is within local scope plus applicable Chat/OpenAI policy/confirmation requirements.

Avoid keeping a broad local-files + open-network surface permanently active. This is not a blanket prohibition on temporarily using Browser + Filesystem or multiple application backends when a concrete task needs them and their scopes are acceptable. Real ordinary-Chat typed Filesystem + Browser use has passed on synthetic scoped data.

## Chat-facing tool semantics

Prefer concrete typed actions with truthful schemas and side-effect semantics.

The generic adaptive `tool_invoke` boundary is not the accepted ordinary-Chat product surface. Its runtime mechanics remain useful diagnostics, but real Chat blocked lifecycle/generic execution before MCP and one generic descriptor cannot truthfully characterize every nested downstream operation.

Do not falsify read-only/destructive/open-world annotations or hide a consequential operation behind a harmless-looking generic tool solely to bypass product review.

Do not expose arbitrary catalog mutation/admin operations such as install/uninstall/update/edit/search as part of the ordinary-Chat baseline.

## Chat permission and safety behavior

App permission mode is an additional user/product control, not the only security boundary.

Observed on the real app:

- `Allow read actions` allowed `read_text_file` without a card and showed a one-time approval card for isolated `write_file`;
- `Allow all actions` allowed typed read/navigate/write without approval;
- a larger composite local-file -> browser -> write workflow was still blocked by OpenAI safety even under full app access, while the same typed actions passed sequentially.

Therefore:

- never infer that full app access disables all OpenAI safety review;
- never diagnose a local backend failure solely from a pre-MCP product safety block;
- do not design the user experience around approval for every low-risk action.

Prefer explicit roots/workspaces, backups, git/rollback, output isolation and bounded tools. Reserve explicit confirmation for genuinely consequential, external or hard-to-reverse effects where practical.

## Secrets

- `CONTROL_PLANE_API_KEY` stays local and is never repository content.
- Long-lived runtime principal uses only permissions required by tunnel runtime (`Tunnels: Read + Use`) unless a separate admin action explicitly requires more.
- Manager stores the runtime key via DPAPI `CurrentUser`; plaintext exists only as needed for child startup.
- Tunnel IDs are local operational configuration.
- Never commit secrets/tunnel IDs or place them in documentation/log screenshots.
- If exposure is suspected, rotate first.

## Bootstrap supply boundary

Accepted bootstrap must:

1. use official `openai/tunnel-client` release channel;
2. pin reviewed release tag/artifact hash;
3. verify official checksum/digest evidence;
4. verify extracted executable before installation;
5. refuse unsafe replacement while the owned binary runs;
6. create tunnel profile via official `tunnel-client init`.

Installed manager/runtime bundle is copied to `%LOCALAPPDATA%\ChatAgentPlatform\app` with verification. Secrets/profile/state/binary live separately.

## Direct reference/diagnostic profiles

`reference` exposes harmless Sequential Thinking.

`files-readonly` scopes one explicit root and removes create/write/edit/move.

`browser-isolated` uses isolated/headless Playwright and removes unsafe code/evaluate/file-upload/direct-network tools.

Their separation is conservative acceptance evidence and fallback diagnostics. It must not be misread as a permanent rule that no legitimate task may ever combine their classes of capability.

## Privileged backend promotion

Before promoting filesystem writes, shell, browser session reuse, local application control, credentials or devices:

1. minimize tools/paths/actions;
2. use scopes/allowlists where supported;
3. prove forbidden tools are absent or denied;
4. document rollback/revocation;
5. avoid secret/environment enumeration by default;
6. decide which operations can be automatic and which consequences need confirmation;
7. test ordinary-Chat product admission separately from local backend health.

## Local specialist inference security

A local model/runtime must remain a bounded capability, not a second autonomous planner.

For local inference candidates:

- prefer local-only serving by default;
- do not expose model-management/install/search/admin actions to ordinary Chat unless specifically needed and accepted;
- select models/variants from a pre-approved/tested set;
- estimate resource use before load where supported;
- use predictable JIT/load/TTL/unload lifecycle;
- treat model output as untrusted capability output that Chat may reason about, not authoritative policy;
- do not let a vision model directly grant itself additional tools or permissions.

LM Studio/`llmster` and `LiquidAI/LFM2.5-VL-3B` remain candidates until target-machine acceptance.

## Lifecycle integrity

- fixed tunnel target must resolve to one intended local 1MCP runtime;
- installed/source manager copies must share one authoritative owner for the fixed runtime;
- an occupied `127.0.0.1:3050` without trustworthy ownership must fail closed instead of accepting another process's health response;
- conflict state must remain observable/recoverable;
- green platform state requires MCP + tunnel readiness;
- startup failure rolls back partial lifecycle;
- task-driven backend activation must clean up idle/disabled backend processes;
- manager/tray must not invent an independent authorization or planning layer.

Functional head `64fa0a27...` implements shared owner state and fail-closed port behavior and passes remote Windows/CI/security checks. Target-machine acceptance is still required before marking this lifecycle issue closed.

## External fallback paths

Historical Yandex/Tailscale routes are not active security architecture. Do not extend them and do not treat public reachability as authorization.
