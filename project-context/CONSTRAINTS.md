# Constraints

1. Ordinary ChatGPT Chat is the primary intelligence layer.
2. Normal operation must not require OpenAI model API calls or Codex/Work as the planner.
3. Standard MCP is the capability boundary.
4. OpenAI Secure MCP Tunnel + official `tunnel-client` is the accepted ChatGPT reachability path; do not reimplement it.
5. The local MCP runtime is replaceable. 1MCP is current default, not product identity.
6. Prefer ready-made official/OSS MCP servers. Project-owned code is allowed only for a measured missing local-program boundary.
7. No generic project-owned job/artifact/secret/policy/confirmation platform unless a future requirement proves ecosystem components insufficient.
8. No public inbound port is required for the normal ChatGPT path.
9. Secrets, runtime API keys and tunnel IDs are local operational data and never repository content.
10. Privileged modules are disabled until their least-privilege permissions and negative tests are accepted.
11. Do not restore legacy code because of sunk cost. Git history is sufficient archival storage.
12. Avoid new paid infrastructure unless the user explicitly chooses it for a concrete benefit.
