# ADR-0004: Hosted Chat → local execution transport

Status: proposed for Stage 4 implementation

## Decision

ChatGPT cannot reach a localhost MCP server directly. OpenAI's supported Secure MCP Tunnel is an excellent future MCP path, but full write/modify MCP in ChatGPT is currently plan-gated and therefore cannot be the only execution path for this project.

The project will use the already-proven Chat → GitHub authenticated path as a narrow command transport to the local Rust binary:

`Chat → private GitHub request ref → agent-platform transport bridge → typed local capability → private GitHub result ref → Chat`.

The bridge is part of the existing `agent-platform.exe`; no second business-logic service is introduced. A foreground/managed bridge process is justified because hosted Chat and the local Windows machine have independent lifecycles.

## Security boundary

- No arbitrary shell, executable, command line or absolute output path is accepted from remote requests.
- Requests use a versioned JSON contract and explicit Project Binding.
- Each request is bound to an expected `main` SHA and expires.
- Only a small allowlist of typed, already-policy-gated platform operations is dispatchable.
- The bridge reads request content with `git show` without checking out the request branch into the user's working tree.
- Results are written from an isolated temporary worktree to a dedicated result ref.
- Execution receipts are persisted locally before publishing, so a retry after a network/push failure re-publishes the same result instead of re-executing the capability.
- Guarded/high-risk capabilities remain subject to their existing policy confirmation rules and are not added merely because a transport exists.

## Why not a public HTTPS tunnel

The local machine does not need an inbound port. Git operations are outbound and reuse the repository's existing authentication. This avoids VPS/ngrok/cloudflared as a mandatory dependency.

## Future MCP compatibility

Secure MCP Tunnel remains an optional future adapter when the user's ChatGPT plan exposes the required MCP action surface. It should connect to the same typed dispatcher rather than duplicate media/business logic.
