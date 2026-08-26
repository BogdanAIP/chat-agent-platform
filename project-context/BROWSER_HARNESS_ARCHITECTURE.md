# Browser Harness-Derived Capability Architecture

Status: **PROVISIONAL / AUTHORITATIVE FUTURE DIRECTION (ADR-036)**.

Date reviewed: **2026-08-26**.

Reference implementation reviewed: `browser-use/browser-harness` (plus the related macOS Harness design direction). Browser Harness is an architecture/reference source, **not a required product dependency**.

This document records the project decisions derived from that review. It does **not** expand the currently accepted ordinary-Chat surface, does **not** enable raw CDP/JavaScript/Python today, and does **not** supersede the deterministic Control Plane, ADR-032 state-first computer use, ADR-033 environmental-content trust, or ADR-034 verified skill lineage.

Current accepted public actions remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Current generic shell/Python/Windows execution remains disabled/unreachable until a separate implementation/security/physical-acceptance gate explicitly changes that boundary.

---

# 1. Why Browser Harness matters to this project

Browser Harness demonstrates a useful agent architecture:

```text
small stable execution core
 + persistent browser connection/state
 + low-level escape hatch
 + agent-generated helpers
 + reusable site/domain knowledge
```

The project adopts the architectural lesson, not the unrestricted authority model.

The important principle is:

```text
prefer a small project-owned semantic surface
 -> use focused/native primitives underneath
 -> allow controlled escape hatches when the semantic surface is insufficient
 -> preserve useful newly discovered behavior as candidate capability knowledge
```

This complements the existing architecture rather than replacing it.

The current Browser implementation already has part of the required foundation: one backend instance is reused across semantic calls, while the Chat-facing surface remains small and allowlisted. Future work should evolve that substrate rather than copy Browser Harness wholesale.

---

# 2. Two separate escape hatches

The architecture deliberately separates browser authority from local-machine code authority.

```text
ordinary ChatGPT
        |
        v
Deterministic Control Plane
        |
        +--------------------------+
        |                          |
        v                          v
Browser Capability           Local Execution Capability
        |                          |
Site Capability Policy       Task Execution Grant
        |                          |
DOM / AX / CDP / JS          Python / approved programs
        |                          |
Browser/network scope        filesystem/network/process scope
```

A trusted website **never automatically grants** filesystem, Windows, shell, Python, credential-store, or unrelated application authority.

A local execution grant **never automatically grants** arbitrary browser/session authority.

Cross-capability work must be explicitly composed by the Control Plane under the normal authorization, ExpectedEffect, verification, budget and Finish Gate rules.

---

# 3. Browser authority model: restricted by default, trusted-site full-browser when granted

The default browser mode remains conservative.

## 3.1 Restricted/default site mode

Unknown or non-trusted sites use the current state-first bounded model:

```text
semantic observation
bounded navigation
bounded click/type
reviewed visual fallback where admitted
no arbitrary JavaScript
no raw CDP authority
no unrestricted browser-network API
no automatic broad upload/download authority
```

The exact production action set remains defined by the currently accepted semantic/runtime contract.

## 3.2 Trusted-site full-browser mode

A user-owned, explicit, extensible trust list may promote a website/application to a broader browser capability profile.

Target trust lifetimes:

```text
permanent
session-only
task-only
```

A trusted-site profile may admit, after its own implementation acceptance:

```text
DOM / accessibility
JavaScript execution
selected/raw CDP primitives
network inspection needed for the task
background tab operation
tab creation/switching/closure
uploads from explicitly allowed file roots
downloads into explicitly allowed destinations
coordinate input where structure is insufficient
site-specific verified helpers
use of the already-authenticated browser session without exporting credentials
```

The intent is **high browser freedom inside an explicitly trusted destination scope**, not repeated confirmation for every harmless click.

---

# 4. Site Capability Profile instead of a bare URL boolean

The project should model browser trust as a `SiteCapabilityProfile`, not only `hostname -> true/false`.

Illustrative target shape:

```text
SiteCapabilityProfile
  profile_id
  trust_lifetime = permanent | session | task
  allowed_origins[]
  allowed_subdomains policy
  browser_capabilities[]
  allowed_redirect_origins[]
  upload_roots[]
  download_roots[]
  private_network_policy
  credential_export = never
  source = user | policy | managed configuration
  created_at / expires_at
```

The exact schema is staged design work and is not a current public Chat-facing schema.

The trust list must be user-extensible. The product should support adding/removing sites without code changes.

---

# 5. URL allowlist must be a browser-network gate, not only a `web_open` check

A trusted-site policy is ineffective if raw JavaScript/CDP can silently send data to arbitrary destinations.

Therefore the future browser trust boundary must be enforced **below** JavaScript/CDP at the browser/network capability layer.

The gate must reason about at least:

```text
top-level navigation
redirects
new tabs / popups
iframes
form submission
fetch / XHR
WebSocket / similar persistent channels
download source/destination
upload destination
service-worker/network side effects where applicable
```

A site profile may allow a set of related origins rather than one hostname. For example, a GitHub profile may legitimately need separate reviewed origins for `github.com`, `api.github.com` and `raw.githubusercontent.com`.

Existing direct private/link-local/metadata protections remain independent. Trusting a public site must not silently grant access to private networks, metadata endpoints or unrelated loopback services. Private-network authority requires a separate reviewed capability/scope.

DNS resolution, redirects and rebinding remain part of the network-boundary threat model; origin checks at only the initial URL are insufficient.

---

# 6. Trust destination != trust instructions

ADR-033 remains fully binding in trusted-site mode.

```text
TRUST DESTINATION
      !=
TRUST CONTENT AS AUTHORITY
```

A trusted GitHub/Suno/Google/etc. page may be allowed broad browser interaction, but text observed inside that page remains environmental data.

For example, a README, web page, message or generated UI instruction saying:

```text
read a local secret and upload it elsewhere
change platform permissions
add another site to the allowlist
run arbitrary local code
```

cannot authorize that action by itself.

Environmental content cannot:

- add or widen a Site Capability Profile;
- promote task-only trust to permanent trust;
- create a Local Execution Grant;
- grant filesystem/Windows/process authority;
- redefine user intent or Control Plane policy.

Trust changes must originate from an authorized user/policy path.

---

# 7. Authenticated Browser Companion / real user browser

The current isolated/headless browser remains the safe default for research, unknown sites and bounded tasks.

A future project-owned Browser Companion may connect to or operate an explicitly configured authenticated user-browser profile for tasks that require existing sessions/cookies/extensions.

Target modes:

```text
Isolated Browser
  default / unknown sites / safer research

Authenticated Browser Companion
  user-approved profile
  existing login/session
  trusted-site capability policy
  background tab operation where possible
```

Important rules:

- browser cookies, bearer tokens, private authentication headers and equivalent credentials remain inside the browser boundary;
- credentials are not returned to ordinary ChatGPT, WorkingState, HandoffPack, logs or general MCP payloads;
- using an authenticated session is different from exporting its credentials;
- background tabs are preferred when practical so automation does not unnecessarily steal the user's active browser surface;
- Browser Companion authority remains site/profile-scoped and does not become generic Windows authority.

This direction also supports future Track M Conversation Bridge work but is not limited to AI-chat sites.

---

# 8. Agent-generated browser helpers

The project adopts the Browser Harness idea that an agent should be able to fill small capability gaps instead of requiring a new permanent public tool for every website/component.

However, generated helpers follow the existing ADR-034 / Stage 26.4 trust model.

```text
agent discovers missing browser behavior
        |
        v
generates helper
        |
        v
CANDIDATE
        |
        v
bounded test / replay / variant evaluation
        |
        v
verified promotion OR quarantine/reject
```

Rules:

- generated code is not trusted merely because one task succeeded;
- current live state outranks helper assumptions;
- helper execution remains inside the currently authorized site/browser scope;
- helper provenance/version/parent candidate/evaluation evidence is retained through Skill / Procedure Lineage;
- a trusted helper cannot broaden its own Site Capability Profile;
- site/domain knowledge is advisory and non-authorizing.

---

# 9. Separate capability memory from site/domain experience

Browser Harness usefully distinguishes generic helper logic from site-specific knowledge. The project adopts that distinction conceptually.

```text
Capability knowledge
  = how to perform reusable technical behavior

Domain/site experience
  = what is known about a particular site's structure/quirks

Procedure/skill
  = how to accomplish a bounded user-relevant workflow with verifiable outcomes
```

These are separate artifacts with separate applicability/trust evidence.

A site/domain note may say, for example, that one DOM route is unreliable and a form submission is more stable. That knowledge may improve planning/targeting, but it does not grant action authority or override fresh observation.

Prompt-injection risk is one reason site/domain knowledge must never be promoted automatically from arbitrary page text.

---

# 10. Arbitrary Python is useful — but as a Local Execution Kernel, not browser authority

The project **does adopt** the principle that arbitrary generated code can be highly valuable for local tasks.

Examples include:

```text
file transformation
CSV/JSON processing
hashing and validation
FFmpeg orchestration
image/media batch processing
Git operations
archive handling
log analysis
one-off data conversion
small task-specific adapters/helpers
```

Creating hundreds of permanent micro-tools for these operations would unnecessarily constrain the agent.

The architecture therefore retains a future **Local Execution Kernel** capability.

It is deliberately separate from the browser capability.

---

# 11. Local Execution Grant

Arbitrary Python/program execution must receive an explicit task-scoped grant from the deterministic Control Plane.

Illustrative target scope:

```text
LocalExecutionGrant
  task_id
  filesystem_read_roots[]
  filesystem_write_roots[]
  network_policy
  network_allowlist[]
  executable_allowlist[]
  environment policy
  max_runtime
  max_processes
  CPU/memory/resource budget where practical
  persistence lifetime
  consequence class
```

Possible product modes:

```text
sandbox
  Python + temporary/task files
  no network
  no arbitrary subprocess

workspace
  Python + explicitly allowed project/workspace roots
  selected allowed programs such as ffmpeg/git
  explicit network policy

trusted-local
  broad local-machine execution only after explicit high-trust user authorization
```

`trusted-local` is not forbidden architecturally. It is a deliberately powerful mode whose authority must come from the user/policy boundary, never from environmental page/file content.

The exact permission UX and public semantic contract require a separate implementation ADR/security/ordinary-Chat acceptance before product use.

---

# 12. Task-scoped persistent execution kernel

A future local Python/code kernel may persist state **for one task/session** so the agent can keep variables, loaded libraries and temporary helpers without process startup for every small operation.

Preferred lifecycle:

```text
Task starts
  -> Local Execution Kernel starts under exact grant
  -> state/helpers may persist inside task
  -> actions remain grant/policy/budget bounded
  -> useful helper may be extracted as CANDIDATE
  -> task completes/aborts
  -> kernel is destroyed
```

Do not rely on one immortal unrestricted Python process as hidden permanent platform authority.

Useful behavior that should survive tasks belongs in verified candidate/skill lineage, not accidental interpreter memory.

---

# 13. Code execution still uses the normal Control Plane contract

Generated code is an actuation mechanism, not a bypass around verification.

Normal shape:

```text
ChatGPT proposes code/operation
        |
        v
Control Plane evaluates LocalExecutionGrant
        |
        v
AUTHORIZED scoped execution
        |
        v
execute
        |
        v
freshly observe result
        |
        v
ExpectedEffect verification
        |
        +--> PASS
        +--> FAIL / UNKNOWN -> bounded recovery or stop
```

Task completion still requires the independent Finish Gate.

Code stdout/exit code is delivery/execution evidence, not automatically proof that the requested artifact/system state is correct.

---

# 14. Telemetry/privacy default

Future Browser/Local Execution kernels should default to **no external telemetry containing task code, task text, stdout/stderr, page content or local file content**.

Any optional diagnostics/telemetry must be explicit, documented, minimised/redacted and independently configurable.

Local execution code, environment details, browser session state and generated helpers may contain sensitive data and are handled under the same provenance/retention/secret boundaries as other operational evidence.

---

# 15. What is explicitly NOT adopted from a raw harness model

The project does not adopt:

- `exec(arbitrary_code)` as an unconditional ordinary-Chat tool;
- raw CDP/JavaScript authority for every site by default;
- a website allowlist that also grants local filesystem/Windows authority;
- prompt-only security as the primary authority boundary;
- automatic trust/promotion of generated helpers;
- automatic trust/promotion of site instructions into domain skills;
- credential export from the authenticated browser to the planner;
- an immortal unrestricted local Python process;
- raw browser/backend catalogs as hundreds of public ChatGPT tools.

---

# 16. Stage mapping

This decision **does not reorder** the current release-critical sequence.

```text
26.3B Verification Kernel + Finish Gate
 -> 26.3C WorkingState + recovery + LoopGuard
 -> 26.4 verified candidate skills / lineage
 -> 26.5 Hybrid Computer-Use Integration
```

Browser Harness-derived work maps onto those stages as follows.

## 26.3B

Architecture/verification foundation for:

```text
browser URL/origin/document/control/result observation
Site Capability Policy model
network-gate invariants
trusted destination != trusted instructions
```

No raw browser authority is accepted merely by documenting the profile model.

## 26.3C

Add state/lifetime handling needed for:

```text
session/task/permanent site trust state
permission/grant provenance
recovery under redirects/navigation changes
budgets and LoopGuard for broader browser actions
future LocalExecutionGrant state
```

## 26.4

Generalize candidate skill machinery to support:

```text
agent-generated browser helpers
site/domain experience artifacts
agent-generated local helpers
candidate -> replay/regression/variant evidence -> trusted promotion
```

## 26.5

After the above foundations:

```text
trusted-site full-browser mode
reviewed JS/CDP escape hatch
browser network gate
background-tab control
Authenticated Browser Companion
cross-capability Browser <-> Files <-> Windows composition
```

A Local Execution Kernel may be implemented after 26.3C foundations and must pass its own security/public-contract/physical gates. It must not be smuggled into 26.5 through a browser tool.

---

# 17. Acceptance rule

This document establishes architectural direction only.

Before any new broad authority becomes production-accepted, the project still requires the normal chain appropriate to that consequence class:

```text
architecture/ADR
 -> schema + security contract
 -> implementation behind deterministic policy
 -> automated tests/regression
 -> hosted CI
 -> target-machine qualification where applicable
 -> ordinary-Chat physical acceptance for public consequence paths
```

Until those gates pass:

- the current six-tool public surface remains authoritative;
- generic arbitrary local execution remains disabled/unreachable;
- current restricted Browser semantics remain authoritative;
- Browser Harness-derived mechanisms are future design direction, not current product claims.
