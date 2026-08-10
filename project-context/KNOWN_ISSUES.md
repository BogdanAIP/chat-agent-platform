# Known Issues

Only unresolved issues for the accepted bridge architecture are listed here.

1. **Privileged MCP modules are not accepted yet.** The reference config intentionally exposes only `sequential_thinking`. Filesystem, shell, browser and application control require Stage 24 security work.

2. **The real module catalog is not selected yet.** Stage 23 must evaluate official/vendor and mature OSS MCP servers before any old project-specific adapter is restored.

3. **OpenAI Secure MCP Tunnel lifecycle is still an external operational dependency.** The official `tunnel-client` must be installed, authenticated with a minimal runtime key and kept healthy. The repository intentionally does not wrap or reimplement its control plane.

4. **Universal Plus availability must not be promised.** The user's real ChatGPT surface passed the custom MCP tunnel round trip, but product availability/plan rules may vary or change.

5. **No end-user Windows manager exists.** Current PowerShell scripts manage only local 1MCP. A GUI/service wrapper is deferred until module lifecycle requirements are known.

6. **Legacy external rollback infrastructure may still exist.** Yandex and the older Tailscale route are no longer repository dependencies, but their live retirement is a separate operational action.

7. **No first stable release is published.** The previous release pipeline was removed because it packaged the superseded universal `agent-platform.exe`. A new release format should be designed only after Stage 23 establishes what this project actually needs to ship.

8. **Support/donation addresses are still pending.** MIT rights remain unconditional and independent of donations.
