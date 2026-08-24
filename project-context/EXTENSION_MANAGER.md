# Optional Extension Manager (1MCP)

Status: **optional internal extension layer; not part of the normal semantic critical path**.

## Why 1MCP remains in the project

The platform does not use 1MCP as the normal ChatGPT transport or as the canonical semantic runtime.

Normal operation is:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

The normal six-tool route must continue to install, start, become READY, recover and pass smoke tests when the optional 1MCP Extension Manager is absent or broken.

1MCP is retained for a different job: managing optional third-party MCP backends behind project-owned semantic facades.

## Responsibility split

### Canonical Semantic Runtime

Owns the stable Chat-facing contract. Stage 26.3A exposes exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Raw third-party MCP tool catalogs are not appended to this surface automatically.

### Deterministic Control Plane

Owns authorization, known procedure progression, checkpoints, verifiers/postconditions, bounded recovery/budgets and fail-closed escalation.

An extension being installed or healthy is never sufficient authorization for an action.

### Optional 1MCP Extension Manager

May own internal extension concerns such as:

```text
discovery/catalog
backend enable/disable
lazy activation
health/status
restart/reload
aggregation of several internal MCP backends
```

It is replaceable. Project architecture must not depend on 1MCP-specific names or transport state outside this boundary.

## Installation boundary

The normal bootstrap does **not** install adaptive/1MCP runtime assets into the baseline manager bundle.

Baseline installation metadata records:

```text
semantic_public_tool_count = 6
extension_manager_included = false
```

The optional Extension Manager is installed explicitly from a reviewed repository checkout:

```powershell
.\scripts\install-extension-manager.ps1 -Action Install
```

Check its state:

```powershell
.\scripts\install-extension-manager.ps1 -Action Status
```

Remove only its optional assets:

```powershell
.\scripts\install-extension-manager.ps1 -Action Remove
```

The installer copies only the reviewed adaptive catalog and compatibility-shim assets. It does not alter `semantic-direct-controller.ps1`, `state/tunnel.json`, normal desired state or the normal Secure MCP Tunnel binding.

## Existing installations and tunnel migration

Older installations may already contain:

```text
%LOCALAPPDATA%\ChatAgentPlatform\config\openai-tunnel-client\local-1mcp.yaml
```

The normal bootstrap may read that file once as a bounded migration source for the already accepted `tunnel_*` id. The canonical persistent tunnel state is then:

```text
%LOCALAPPDATA%\ChatAgentPlatform\state\tunnel.json
```

After migration, `local-1mcp.yaml` is not the normal semantic source of truth.

## Adding a future MCP backend

A new MCP backend must not be exposed to ChatGPT merely because 1MCP can discover or start it.

Required promotion sequence:

```text
candidate backend
 -> pin/version + provenance review
 -> isolated Extension Manager catalog entry
 -> least-privilege configuration
 -> backend-specific acceptance/security tests
 -> project-owned typed semantic facade
 -> Control Plane authorization/verifier integration where actions have consequences
 -> hosted acceptance
 -> physical acceptance where applicable
 -> only then eligible for normal product use
```

Prefer narrow project-owned semantic operations over publishing a backend's complete raw tool inventory.

## CI separation

Required baseline workflows prove the six-tool direct semantic platform without starting 1MCP.

1MCP/adaptive runtime checks live in:

```text
.github/workflows/extension-manager.yml
```

That workflow is intentionally named:

```text
Optional Extension Manager Acceptance
```

It verifies:

- adaptive catalog pins and disabled-by-default policy;
- opt-in installer `Install -> Status -> Remove` lifecycle;
- legacy/internal 1MCP runtime compatibility;
- lazy adaptive backend activation/deactivation;
- no claim that 1MCP is a baseline semantic dependency.

An Extension Manager regression is important evidence for extension capability, but it must not be used to infer that the canonical direct six-tool runtime is unhealthy.

## Non-negotiable rules

- 1MCP is not the normal Chat-facing transport.
- 1MCP is not the source of truth for the normal tunnel id.
- 1MCP is not required by normal bootstrap/start/health/smoke.
- installing an extension does not grant authorization.
- raw extension tools are not automatically public.
- normal semantic readiness is evaluated independently of Extension Manager readiness.
- failure of an optional extension must not take down the canonical six-tool runtime.
