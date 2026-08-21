# Cost Policy

- Ordinary ChatGPT Chat remains the current general intelligence/planning surface chosen by the user.
- The bridge does not require OpenAI model API inference calls.
- The OpenAI runtime key used by official `tunnel-client` is Secure MCP Tunnel **infrastructure control-plane authentication**. It must not be silently reused for model API calls.
- That OpenAI/tunnel “control plane” terminology is unrelated to the project's planned **deterministic local execution Control Plane** (`CONTROL_PLANE.md`). The local Control Plane is task/procedure state, authorization, verification, checkpoint and bounded recovery logic; it does not need an additional paid AI service.
- The baseline product must require **zero new mandatory SaaS subscriptions** beyond software/services the user independently chooses to own/subscribe to.
- Prefer official local tools and mature free/open-source components when they meet quality/security requirements.
- A weak free MCP must not be chosen over a high-quality local API merely to avoid a thin adapter.
- Free SaaS tiers are optional conveniences, not architecture; limits/pricing can change.
- Paid cloud/VPS/GPU/API services are optional and require a concrete user-approved reason.
- Prefer pay-per-use for genuinely expensive remote operations over accumulating recurring subscriptions.
- Do not create persistent cloud infrastructure for functions that can run locally or through the official tunnel.
- Do not perform an operation with unknown cost or silently trigger a purchase/subscription.
- Local file access, browser automation, desktop control, deterministic procedure execution and local media processing must have a no-extra-subscription baseline path.
- Future local planner Track P is optional research. Its model/runtime must be selected by measured benefit and target hardware/resource evidence, not as a mandatory paid dependency.

Selection details: `MODULE_SELECTION_POLICY.md`. Current candidates/status: `MODULE_CATALOG.md`.
