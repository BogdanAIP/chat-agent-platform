# Known Issues — Bridge v1.5

Only current unresolved risks are listed here. Historical implementation details belong in `CURRENT_STATE.md`.

1. **Native MCP from the user's actual ChatGPT Chat surface is not yet proved.** The legacy development plugin already proved ChatGPT -> Windows execution, and Tailscale already proved public HTTPS -> localhost. The missing gate is one real ordinary-Chat invocation through a standard public `/mcp` endpoint.

2. **1MCP compatibility with this exact ChatGPT development-app surface is not yet accepted.** The pilot is prepared with pinned 1MCP and a harmless official reference server. If tool scan/call fails, determine whether the cause is protocol version, authentication, transport behavior, or ChatGPT account policy before writing custom compatibility code.

3. **Public OpenAI plan documentation and the user's observed account capabilities do not fully align.** The real account already has a development plugin with write-capable local actions, but public OpenAI documentation does not guarantee the same full-MCP capability for every Plus account. Do not advertise universal Plus compatibility until it is officially documented or independently reproduced.

4. **The pilot Funnel on HTTPS `8443` is intentionally unauthenticated.** It is safe only because the pilot exports the non-privileged Sequential Thinking reference tool. The listener must be stopped after the test. Filesystem, shell, browser, application-control, secrets or other privileged modules must not be added until an authentication/authorization profile is accepted.

5. **The permanent local MCP runtime is not selected yet.** 1MCP is the first candidate. ToolHive is the first fallback for stronger isolation/security/governance/protocol translation; agentgateway is a possible protocol/security edge. Do not carry all of them as permanent dependencies.

6. **The repository contains much more custom infrastructure than the new target requires.** `agent-platform.exe`, custom ingress/relay, universal policy/job/artifact/confirmation systems and media-specific workflows remain present until the off-the-shelf bridge is proved. They must then be classified and reduced rather than silently remaining mandatory baggage.

7. **Yandex/polling and custom `/gpt` are legacy compatibility paths, not target architecture.** They must not receive new feature development. Removal waits until native MCP through a mature runtime passes the real ChatGPT acceptance gate.

8. **The current working Tailscale Funnel is public internet reachability.** A tunnel is not an authorization boundary. Before privileged modules are enabled, negative public-access tests and ChatGPT-side permission behavior must be documented.

9. **No thin end-user configurator exists yet.** Manual scripts/configuration are acceptable until the bridge/runtime/module model is proved. Building a GUI before that would risk wrapping the wrong runtime architecture.

10. **First versioned release/tag has not been published.** Existing release/supply-chain work remains valid, but a release should wait until the v1.5 runtime direction is accepted so the project does not publish a now-deprecated universal core as its first stable product shape.

11. **Support/donation addresses are still pending.** MIT rights remain unconditional and independent of donations.
