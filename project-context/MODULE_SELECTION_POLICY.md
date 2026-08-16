# Module Selection Policy

## Product rule

The baseline Chat-to-Local Bridge must work with **zero new mandatory SaaS subscriptions**. A module must be technically good enough, maintainable, secure enough for its intended scope and economically sane.

## Selection order

1. official/vendor local MCP or mature official local runtime;
2. mature open-source MCP/runtime with acceptable license/maintenance;
3. official/vendor local API or CLI behind the smallest focused MCP/typed adapter;
4. mature generic local automation (for example Windows UI Automation) as fallback;
5. paid API/SaaS only for genuinely remote/expensive capabilities explicitly chosen by the user.

Do not implement a custom adapter merely because it is possible. Do not adopt a weak MCP merely because it already exists.

## Mandatory gates

A candidate cannot become a supported/default backend until applicable gates pass:

- **Quality:** reliable enough for the target operation; structured API preferred over pixels/coordinates where possible.
- **Cost:** no hidden mandatory recurring SaaS dependency in the baseline path.
- **License:** compatible and recorded.
- **Maintenance:** upstream not clearly abandoned.
- **Security:** useful scopes/disabled tools/allowlists or another measured containment mechanism exist.
- **Locality:** local data stays local unless the operation explicitly needs external access.
- **Supply channel:** selected version/artifact actually exists where installation expects it.
- **Pinning:** tested published version or immutable source/release pin.
- **Evidence:** install/start/health/tool-call behavior tested before promotion.
- **Lifecycle:** backend can be started/stopped predictably and does not require permanent residence unless technically necessary.
- **Chat admission:** a locally healthy tool is not product-accepted until the actual Chat-facing typed action is admitted and usable where ordinary-Chat use is required.

## Chat-facing typed surface rule

Adding a backend should normally change local catalog/config/acceptance evidence, not create another ChatGPT app/plugin.

Backend registration is not activation. Start the backend(s) needed by the task; allow multiple active backends for workflows that need them; stop idle backends when safe.

Do not expose hundreds of unrelated backend tools directly to Chat at once. Stage 24 observed effective snapshot truncation around 20 actions in the tested app, but this is not an official universal platform constant.

Prefer concrete typed actions with truthful schemas and semantics. The generic adaptive `tool_list`/`tool_schema`/`tool_invoke` contract remains useful diagnostic infrastructure but is not the accepted ordinary-Chat product surface because real Chat blocked its lifecycle/generic execution path before MCP.

If a focused capability projection/facade is required to fit product constraints, it must:

- expose exact typed operations rather than one arbitrary nested dispatcher;
- remain small and deterministic;
- preserve backend scopes/disabled-tool boundaries;
- not become a planner/workflow engine/generic replacement MCP platform;
- be justified by measured Chat/product behavior and ordinary-Chat acceptance.

Direct profiles remain useful for acceptance/fallback but are not the desired scaling mechanism for every application.

## Local specialist model/runtime rule

A local model is a capability backend, not the Chat planner.

For local inference runtime managers and models, add these gates:

- **Capability match:** vision/OCR/grounding/etc. must match the intended typed capability.
- **Hardware fit:** use measured runtime estimates/benchmarks on the target machine; do not hard-code a quantization from guesswork.
- **Variant selection:** prefer the highest-quality tested variant that fits RAM/VRAM/latency guardrails.
- **Runtime lifecycle:** support predictable load/JIT/unload/TTL/eviction behavior.
- **Replaceability:** the platform contract must not depend on one model/runtime identifier.
- **Privacy:** local inference remains local unless the user explicitly chooses remote fallback.

LM Studio/`llmster` is the first runtime-manager candidate for Stage 25 because its current documented CLI/server behavior includes local model listing/loading, resource estimation before load, GPU-offload control, JIT loading, TTL and auto-eviction.

`LiquidAI/LFM2.5-VL-3B` is the first preferred local-vision model candidate. Official Liquid AI release material documents screen/UI understanding, OCR/document/chart understanding, grounding, multi-image input and GGUF/llama.cpp plus ONNX support. It remains unaccepted until target-machine benchmarking.

## Paid layer

Paid services are optional accelerators, never hidden prerequisites.

- no automatic purchase/subscription;
- no unknown-cost execution;
- no paid dependency just to open files, browse, automate installed software, run accepted local models or process local media;
- prefer pay-per-use for genuinely expensive remote work;
- free SaaS tiers are optional conveniences, not architecture.

## Adapter rule

When a strong local API exists but no acceptable MCP does, write the smallest useful typed adapter around that API. It must not grow into another planner, workflow engine, generic gateway, secret store, policy platform or bespoke model-serving framework.
