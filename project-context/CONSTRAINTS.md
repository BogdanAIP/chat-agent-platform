# Constraints

1. Ordinary ChatGPT Chat is the primary intelligence/planning layer.
2. Normal product operation must not require OpenAI model API calls or Codex/Work as the planner.
3. Standard MCP is the capability boundary.
4. OpenAI Secure MCP Tunnel + official `tunnel-client` is the accepted ChatGPT reachability path; do not reimplement it.
5. The local MCP runtime is replaceable. 1MCP is current infrastructure, not product identity.
6. Prefer ready-made official/OSS MCP servers. Project-owned adapters require a measured missing local-program boundary.
7. No generic project-owned gateway/registry/job/artifact/secret/policy/confirmation/workflow platform unless evidence proves ecosystem components insufficient.
8. No public inbound port is required for the normal ChatGPT path.
9. Secrets, runtime API keys and tunnel IDs are local operational data and never repository content.
10. Privileged operations require scoped permissions/negative tests; security must not be interpreted as a blanket ban on useful multi-backend workflows.
11. The target steady-state UX must not require one separate ChatGPT app/plugin per local backend.
12. The target steady-state UX should not require routine Refresh merely because a pre-approved local backend is added/enabled; Stage 24 adaptive acceptance is intended to prove this and is not yet complete.
13. Backend registration and backend process activation are separate. Do not run the entire catalog permanently.
14. Multiple backend processes may be active when the actual task requires them.
15. Do not expose arbitrary MCP install/uninstall/update/edit/search controls to ordinary Chat as part of the adaptive baseline.
16. Do not restore legacy code because of sunk cost; Git history is sufficient archival storage.
17. Avoid new paid infrastructure unless the user explicitly chooses it for a concrete benefit.
18. Real Windows/ordinary-Chat acceptance may only be marked passed from actual target-machine/user-surface evidence.
