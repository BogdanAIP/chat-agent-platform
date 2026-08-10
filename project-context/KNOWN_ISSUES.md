# Known Issues — Bridge v1.6

Only current unresolved risks are listed here. Historical acceptance evidence belongs in `CURRENT_STATE.md` and `BRIDGE_PILOT.md`.

1. **Privileged-module security profile is not accepted yet.** Stage 21 proved only the harmless Sequential Thinking tool. Filesystem, shell, browser, application-control, secrets and other privileged modules must wait for explicit exposure profiles, least-privilege rules, ChatGPT permission checks and negative-access tests.

2. **OpenAI Secure MCP Tunnel introduces a runtime credential dependency.** The official tunnel-client needs a runtime API key with `Tunnels Read + Use`. Secrets must remain outside git, logs and documentation; rotation/recovery/startup behavior still needs to be productized.

3. **The repository contains much more custom infrastructure than the accepted target requires.** `agent-platform.exe`, custom ingress/relay, universal policy/job/artifact/confirmation systems and media-specific workflows remain present. Stage 22 must classify each component as remove, extract, retain or archive/reference rather than silently shipping all historical code.

4. **Yandex/polling and custom `/gpt` are legacy compatibility paths, not target architecture.** They must not receive new feature development. The existing HTTPS `443`/Yandex route remains rollback evidence until a separate cleanup decision.

5. **Tailscale is now optional/fallback rather than primary ChatGPT transport.** The temporary public Funnel `8443` pilot should not become a permanent privileged ingress. The accepted primary path is OpenAI Secure MCP Tunnel.

6. **1MCP is accepted but still replaceable.** It passed the real ChatGPT round trip and is the current default local runtime. ToolHive, agentgateway or Docker MCP Toolkit should only be introduced for a concrete measured gap; carrying several runtimes permanently would recreate the tool-zoo problem.

7. **No thin end-user Windows configurator exists yet.** Manual runtime/tunnel setup is acceptable while Stage 22-24 settle the permanent module/security model. A GUI should wrap the accepted components rather than recreate their runtime behavior.

8. **Public ChatGPT plan documentation can lag observed account behavior.** This user's account successfully created and invoked a custom MCP app through Secure MCP Tunnel. Do not advertise universal Plus compatibility solely from this single accepted environment.

9. **First versioned release/tag has not been published.** Existing release/supply-chain work remains valid, but the first release should reflect the reduced v1.6 bridge architecture rather than the superseded universal Rust core.

10. **Support/donation addresses are still pending.** MIT rights remain unconditional and independent of donations.
