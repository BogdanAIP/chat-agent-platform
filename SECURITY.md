# Security Policy

## Supported versions

Until the first versioned release is published, security fixes target the current `main` branch.

After the first release, this file must be updated explicitly if more than one release line is supported. Do not infer long-term support from the existence of an old tag.

## Reporting a vulnerability

Do **not** publish secrets, access tokens, credentials, private endpoints, exploit payloads, or detailed proof-of-concept instructions in a public GitHub issue.

Preferred reporting path:

1. If this repository's **Security** tab offers **Report a vulnerability**, use that private GitHub channel.
2. If no private reporting control is available, open a minimal public issue stating only that you need a private channel for a security report. Do not include sensitive technical details in that issue.

There is currently no guaranteed response-time SLA. Reports are handled on a best-effort basis, with priority given to issues that can expose credentials, bypass policy/confirmation boundaries, execute unintended local capabilities, corrupt artifact identity, or compromise the release/supply-chain path.

## Scope

Security-sensitive surfaces include:

- `agent-platform.exe` policy and capability enforcement;
- Project Binding and remote allowlists;
- relay authentication (`MCP_TOKEN` / `X-MCP-Token` and local agent credentials);
- Windows Credential Manager integration and secret ACLs;
- Artifact Store identity, staging, recovery, and job execution ownership;
- guarded confirmation and replay protection;
- Yandex API Gateway / Cloud Function relay transport;
- GitHub Actions, dependency policy, SBOM, license bundle, provenance, and release packaging.

The project intentionally does not accept arbitrary shell, FFmpeg, Python, REAPER, browser, or distribution command surfaces as remote capabilities.

## Secret handling

Never commit or paste real relay tokens, Yandex credentials, GitHub credentials, private keys, or other secrets into repository files, pull requests, issues, logs, acceptance reports, or chat messages.

If a credential may have been exposed, rotate/revoke it first and treat repository cleanup as a separate follow-up. Removing a secret from the latest commit alone does not remove it from Git history.
