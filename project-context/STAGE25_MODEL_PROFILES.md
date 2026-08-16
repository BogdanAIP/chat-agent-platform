# Stage 25 local-vision model profiles

Status: active benchmark configuration.

The Stage 25 grounding orchestrator supports explicit model profiles so target-machine evidence can be compared without silently changing model artifacts.

## `lfm25-vl-3b-q4km`

Directory:

```text
%LOCALAPPDATA%\ChatAgentPlatform\stage25\models\LFM2.5-VL-3B-GGUF
```

Artifacts:

```text
LFM2.5-VL-3B-Q4_K_M.gguf
  bytes: 1674454240
  sha256: 83c18dfba02c75769cdd63f73e37c343400e82d434ff1b14bcc1cb02fcf2f5f2

mmproj-LFM2.5-VL-3B-Q8_0.gguf
  bytes: 583109120
  sha256: 8ba27050dc88737db66b856d3b74e0e6cf54bee35fa4d9d9808f69ee556bbd43
```

This profile remains available for machines with sufficient memory, but it is no longer a safe default candidate for the 7.68 GB target laptop. With Chrome closed and about 3.18 GB free before launch, the latest staged probe observed only 0.18 GB free after server load and stopped before the selected Direct cases could run.

## `lfm25-vl-1.6b-q4km`

Official source repository: `LiquidAI/LFM2.5-VL-1.6B-GGUF`.

Directory:

```text
%LOCALAPPDATA%\ChatAgentPlatform\stage25\models\LFM2.5-VL-1.6B-GGUF
```

Artifacts:

```text
LFM2.5-VL-1.6B-Q4_K_M.gguf
  bytes: 730896256
  sha256: aefc3c97c9eb30d9c0dd6af4c38250f5f5106b57c8cf92de7914c7d0a9c94da2

mmproj-LFM2.5-VL-1.6b-Q8_0.gguf
  bytes: 583109888
  sha256: 2ce89e610c56f3198ece2b86cf61743a08b9307279c89125eb2412ebb908689d
```

The orchestrator validates both exact byte size and SHA256 before starting llama.cpp. Model download remains a separate preparation step; inference never downloads or replaces model artifacts.

## Target acceptance order

1. Verify the 1.6B pair locally.
2. Close Chrome and establish a safe pre-run RAM margin.
3. Run Direct at `ctx=1024` on `labeled-primary-button` and `absent-target`.
4. Accept quality evidence only if requests actually complete with valid schema-constrained outputs.
5. Broaden Direct coverage only after memory and correctness are both acceptable.
6. Evaluate faithful Mark-Grid separately because its measured two-pass prompt requires a larger context and therefore a different memory envelope.

The public Chat-facing semantic tool surface is unchanged by model-profile benchmarking.
