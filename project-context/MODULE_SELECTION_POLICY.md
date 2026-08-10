# Module Selection Policy

## Product rule

The baseline Chat-to-Local Bridge must work with **zero new mandatory SaaS subscriptions**.

A module is acceptable only when it is both technically good enough and economically sane. "Free" is not enough if it is unreliable; "professional" is not enough if it silently creates a chain of recurring subscriptions.

## Selection order

For every local capability, evaluate candidates in this order:

1. official/vendor MCP that runs locally without a recurring service dependency;
2. mature open-source MCP with a permissive license and active maintenance;
3. official/vendor local API or CLI wrapped by a thin project-owned MCP adapter;
4. mature generic local automation (for example Windows UI Automation) as a fallback;
5. paid API/SaaS only when the task genuinely requires a remote expensive capability and the user explicitly chooses it.

Do not implement a custom adapter merely because we can. Do not adopt a weak community MCP merely because it already exists.

## Mandatory gates

A candidate cannot become a default module until all applicable gates pass:

- **Quality:** deterministic enough for the target operation; structured API preferred over pixels/coordinates.
- **Cost:** no mandatory recurring SaaS fee in the baseline path.
- **License:** compatible with use/distribution; license recorded in the catalog.
- **Maintenance:** upstream is not archived/abandoned and has credible recent activity.
- **Security:** least-privilege exposure is possible; dangerous tools can be disabled or scoped.
- **Locality:** local files, installed software and local execution stay local unless the operation explicitly requires external access.
- **Supply channel:** the selected version must actually exist in the channel used to install it (npm, PyPI, GitHub Release, vendor installer). A newer version string in an unreleased source-tree `package.json` is not install evidence.
- **Pinning:** production configs pin a tested published version or immutable release.
- **Evidence:** install/start/health/tool-call behavior is tested before promotion.

## Paid layer

Paid services are optional accelerators, never hidden prerequisites. Examples include video generation, rented GPU and specialist premium APIs.

Rules:

- no automatic purchase or subscription;
- no unknown-cost execution;
- no paid dependency in order to open files, browse, automate installed desktop software, process media locally or use the bridge itself;
- prefer pay-per-use for genuinely expensive remote work over accumulating subscriptions;
- a free SaaS tier is treated as optional, not as architecture, because limits/pricing can change.

## Adapter rule

When an official high-level API exists but no acceptable MCP exists, write the smallest useful adapter around that API. The adapter must not grow into another planner, workflow engine, generic transport, secret store or policy platform.

## Tool-surface rule

Do not expose hundreds of unrelated tools to ChatGPT at once. Use 1MCP tags/filters/presets and, where supported, `disabledTools` or progressive discovery so a task sees only the relevant module surface.
