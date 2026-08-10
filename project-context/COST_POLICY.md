# Cost Policy

- Ordinary ChatGPT Chat remains the intelligence surface chosen by the user.
- The bridge does not require OpenAI model API inference calls.
- The OpenAI runtime key used by official `tunnel-client` is control-plane authentication for Secure MCP Tunnel; bridge code must not silently reuse it for model API calls.
- Prefer free/open-source local MCP runtimes and modules when they meet quality and security requirements.
- Paid cloud/VPS/GPU services are optional and require a concrete user-approved reason.
- Do not create persistent cloud infrastructure for functions that can run locally or through the official tunnel.
