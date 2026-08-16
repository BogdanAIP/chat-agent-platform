# Stage 25 — Target Windows local-vision benchmark evidence

Status: **ACTIVE EVIDENCE / 2026-08-16**

This file records measured target-machine evidence for the first Stage 25 local-vision candidate. It is benchmark evidence, not a permanent vendor/runtime commitment.

## Target machine

```text
CPU: 11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz
Logical CPUs: 8
RAM: 7.68 GB
GPU: Intel(R) Iris(R) Xe Graphics
GPU driver: 31.0.101.5186
```

`llama.cpp --list-devices` exposes:

```text
Vulkan0: Intel(R) Iris(R) Xe Graphics (3929 MiB, 3536 MiB free)
```

The Windows `AdapterRAM` value of 128 MB is not treated as dedicated usable VRAM for this integrated GPU.

## Runtime and artifacts

Installed runtime:

```text
llama.cpp package: ggml.llamacpp
release: b10448
version: 0.1.0-dev
build: 10448
commit: ad1de39e0
Windows x86_64 Vulkan build
```

Verified official model pair:

```text
LFM2.5-VL-3B-Q4_K_M.gguf
  bytes: 1674454240
  sha256: 83c18dfba02c75769cdd63f73e37c343400e82d434ff1b14bcc1cb02fcf2f5f2

mmproj-LFM2.5-VL-3B-Q8_0.gguf
  bytes: 583109120
  sha256: 8ba27050dc88737db66b856d3b74e0e6cf54bee35fa4d9d9808f69ee556bbd43
```

Both artifacts were accepted only after exact size and SHA256 verification.

## First controlled CPU-only load

Configuration:

```text
main model: CPU only
mmproj: CPU only
ctx-size: 1024
batch-size: 128
ubatch-size: 64
KV cache: q8_0 / q8_0
```

Observed:

```text
SERVER_READY=True
LOAD_SECONDS=15.22
MAX_SERVER_WORKING_SET_MB=2238.2
MAX_SERVER_PRIVATE_MB=2054.4
MIN_RAM_FREE_GB=0.41
MIN_VIRTUAL_FREE_GB=3.81
MAX_PAGEFILE_USED_MB=1041
STAGE25_LFM25_VL_3B_CPU_LOAD=PASS
```

Conclusion: the full 3B Q4_K_M + Q8 projector pair loads successfully on the 7.68 GB target, but memory headroom is tight.

## First real deterministic vision acceptance

Test image contained:

```text
title: STAGE25 VISION TEST
red circle
blue square
code: A7-42
```

The first HTTP wrapper lost the response file, but llama-server logs proved that the request reached the multimodal model and completed generation. The wrapper was corrected to use `ProcessStartInfo.ArgumentList`, after which the full response was captured.

Accepted result:

```text
TITLE=STAGE25 VISION TEST; CIRCLE=red; SQUARE=blue; CODE=A7-42
```

Observed:

```text
CURL_EXIT_CODE=0
PROMPT_TOKENS=218
COMPLETION_TOKENS=27
TOTAL_TOKENS=245
VISION_WALL_SECONDS=15.09
MIN_RAM_FREE_GB=0.40
MIN_VIRTUAL_FREE_GB=3.66
MAX_PAGEFILE_MB=1223
MAX_SERVER_WORKING_SET_MB=2539.1
VISION_SEMANTIC_EXPECTED=True
STAGE25_LFM25_VL_3B_VISION_CALL=PASS
```

This closes basic feasibility: the selected 3B model performs a real local multimodal request correctly on the target laptop.

## Vulkan comparison

### Main-model partial offload: 8 layers to Iris Xe

Configuration:

```text
main model GPU layers: 8
mmproj: CPU
KV: CPU
op offload: disabled
```

Observed:

```text
VULKAN_LOAD_SECONDS=12.80
VULKAN_VISION_SECONDS=26.53
VULKAN_MIN_RAM_FREE_GB=0.61
VULKAN_MIN_VIRTUAL_FREE_GB=2.92
VULKAN_MAX_PAGEFILE_MB=1207
VULKAN_MAX_WORKING_SET_MB=2544.3
VISION_SEMANTIC_EXPECTED=True
STAGE25_LFM25_VL_3B_VULKAN8=PASS
```

Compared with the accepted CPU baseline, 8-layer Vulkan offload was materially slower. Do not use it as the normal configuration from this evidence.

### Projector-only Vulkan offload

Configuration:

```text
main model GPU layers: 0
mmproj: Vulkan0
KV: CPU
op offload: disabled
```

The log confirmed real projector offload:

```text
clip_ctx: CLIP using Vulkan0 backend
load_tensors: offloaded 0/31 layers to GPU
```

Observed:

```text
MMPROJ_GPU_LOAD_SECONDS=6.15
MMPROJ_GPU_VISION_SECONDS=20.19
MMPROJ_GPU_MIN_RAM_FREE_GB=0.80
MMPROJ_GPU_MIN_VIRTUAL_FREE_GB=3.16
MMPROJ_GPU_MAX_PAGEFILE_MB=1173
MMPROJ_GPU_MAX_WORKING_SET_MB=2348.2
VISION_SEMANTIC_EXPECTED=True
STAGE25_LFM25_VL_3B_MMPROJ_VULKAN=PASS
```

Projector-only Vulkan reduced RAM pressure and improved cold load time, but inference remained slower than CPU-only. Keep it as a possible memory-pressure fallback, not the default fast path.

## CPU thread benchmark

Initial single-run comparison:

| Threads | Load s | Vision s | Min free RAM GB | Max working set MB |
|---:|---:|---:|---:|---:|
| 4 | 7.21 | 15.20 | 0.42 | 2859.9 |
| 6 | 6.15 | 14.20 | 0.48 | 3181.5 |
| 8 | 5.13 | 14.25 | 0.43 | 3439.9 |

All three produced the expected semantic answer.

Because 6 and 8 were nearly tied, the final comparison used six interleaved cold runs in the order `6, 8, 8, 6, 6, 8`.

Raw final runs:

| Run | Threads | Load s | Vision s | Min free RAM GB | Max working set MB | Max pagefile MB |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6 | 5.67 | 14.12 | 0.45 | 2908.1 | 1206 |
| 2 | 8 | 5.67 | 13.84 | 0.44 | 3194.8 | 1440 |
| 3 | 8 | 5.13 | 14.11 | 0.44 | 3440.2 | 1416 |
| 4 | 6 | 5.61 | 14.69 | 0.29 | 3439.4 | 1373 |
| 5 | 6 | 5.14 | 14.13 | 0.45 | 3361.5 | 1292 |
| 6 | 8 | 5.65 | 13.53 | 0.43 | 3328.0 | 1531 |

Median summary:

| Threads | Median load s | Median vision s | Best vision s | Worst vision s | Worst min free RAM GB | Peak working set MB |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 5.65 | **13.84** | 13.53 | 14.11 | 0.43 | 3440.2 |
| 6 | 5.61 | 14.13 | 14.12 | 14.69 | 0.29 | 3439.4 |

Marker:

```text
STAGE25_LFM25_VL_3B_CPU_THREAD_FINAL=PASS
```

### Current benchmarked llama.cpp policy

For this exact target/model/test:

- use CPU-only model + CPU-only projector as the normal fast path;
- use 8 inference/batch threads as the current measured winner;
- keep `ctx-size=1024` for the initial bounded adapter until representative workloads justify larger context;
- do not use 8-layer Iris Xe model offload as the default;
- keep projector-only Vulkan as a possible memory-pressure fallback because it increases free-RAM headroom, despite slower inference.

The 8-thread choice is evidence-backed for this deterministic test, but it is still subject to representative UI/OCR/chart benchmark tasks before final runtime acceptance.

## Current conclusion

`LiquidAI/LFM2.5-VL-3B` Q4_K_M is no longer merely a feasibility candidate on the target laptop. It has passed:

- exact artifact verification;
- controlled model load;
- real multimodal inference;
- deterministic semantic correctness;
- process cleanup;
- CPU/Vulkan placement comparison;
- repeated CPU thread tuning.

The next engineering work should stop micro-tuning the same synthetic image and move to representative task quality tests and the deterministic vendor-neutral local-vision adapter boundary. ONNX/OpenVINO remains a runtime-format comparison candidate; it should be evaluated only with complete artifact/shard accounting and the same representative benchmark set.