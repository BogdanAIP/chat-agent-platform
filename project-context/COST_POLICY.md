# Cost Policy

- Ordinary ChatGPT Chat remains the intelligence surface chosen by the user.
- The bridge does not require OpenAI model API inference calls.
- The OpenAI runtime key used by official `tunnel-client` is control-plane authentication for Secure MCP Tunnel; bridge code must not silently reuse it for model API calls.
- The baseline product must require **zero new mandatory SaaS subscriptions** beyond software/services the user has independently chosen to own or subscribe to.
- Prefer official local tools and mature free/open-source MCP modules when they meet quality and security requirements.
- A weak free MCP must not be chosen over a high-quality official local API merely to avoid writing a thin adapter.
- Free SaaS tiers are optional conveniences, not architecture: limits and pricing can change.
- Paid cloud/VPS/GPU/API services are optional and require a concrete user-approved reason.
- Prefer pay-per-use for genuinely expensive remote operations over accumulating recurring subscriptions.
- Do not create persistent cloud infrastructure for functions that can run locally or through the official tunnel.
- Do not perform an operation with unknown cost or silently trigger a purchase/subscription.
- Local file access, browser automation, installed desktop application control and local media processing must have a no-extra-subscription path.

Selection details live in `MODULE_SELECTION_POLICY.md` and current candidates in `MODULE_CATALOG.md`.
