# Module Selection Policy

## Product rule

The baseline Chat-to-Local Bridge must work with **zero new mandatory SaaS subscriptions**. A module must be technically good enough, maintainable, secure enough for its intended scope and economically sane.

## Selection order

1. official/vendor local MCP;
2. mature open-source MCP with acceptable license/maintenance;
3. official/vendor local API or CLI behind the smallest focused MCP adapter;
4. mature generic local automation (for example Windows UI Automation) as fallback;
5. paid API/SaaS only for genuinely remote/expensive capabilities explicitly chosen by the user.

Do not implement a custom adapter merely because it is possible. Do not adopt a weak MCP merely because it already exists.

## Mandatory gates

A candidate cannot become a supported/default backend until applicable gates pass:

- **Quality:** reliable enough for the target operation; structured API preferred over pixels/coordinates.
- **Cost:** no hidden mandatory recurring SaaS dependency in the baseline path.
- **License:** compatible and recorded.
- **Maintenance:** upstream not clearly abandoned.
- **Security:** useful scopes/disabled tools/allowlists or another measured containment mechanism exist.
- **Locality:** local data stays local unless the operation explicitly needs external access.
- **Supply channel:** selected version/artifact actually exists where installation expects it.
- **Pinning:** tested published version or immutable source/release pin.
- **Evidence:** install/start/health/tool-call behavior tested before promotion.
- **Lifecycle:** backend can be started/stopped predictably and does not require permanent residence unless technically necessary.

## Adaptive catalog rule

The target Stage 24 architecture keeps one stable Chat-facing discovery/invocation contract and a **pre-approved local backend catalog**.

Adding a backend should normally change local catalog/config/acceptance evidence, not create another ChatGPT app/plugin.

Backend registration is not activation. Start the backend(s) needed by the task; allow multiple active backends for workflows that need them; stop idle backends when safe.

Ordinary Chat may receive narrow lifecycle controls for the approved catalog, but must not receive arbitrary install/uninstall/update/edit/search controls in the baseline.

## Tool-surface rule

Do not expose hundreds of unrelated backend tools directly to Chat at once. Prefer progressive/lazy discovery (`tool_list`, `tool_schema`, `tool_invoke`) and backend-level disabled tools/scopes.

Direct profiles remain useful for acceptance/fallback but are not the desired scaling mechanism for every application.

## Paid layer

Paid services are optional accelerators, never hidden prerequisites.

- no automatic purchase/subscription;
- no unknown-cost execution;
- no paid dependency just to open files, browse, automate installed software or process local media;
- prefer pay-per-use for genuinely expensive remote work;
- free SaaS tiers are optional conveniences, not architecture.

## Adapter rule

When a strong local API exists but no acceptable MCP does, write the smallest useful adapter around that API. It must not grow into another planner, workflow engine, generic gateway, secret store or policy platform.
