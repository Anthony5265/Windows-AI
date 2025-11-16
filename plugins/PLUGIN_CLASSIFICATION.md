# Plugin Classification (November 2025)

This file captures the current plugin maturity levels so it is immediately clear
which items count as *production-ready* versus placeholders. It mirrors the
truths documented in `HONEST_REPO_ASSESSMENT.md` and
`NEW_MASTER_ROADMAP.md`.

## Tier 1 – Production Ready (30 items)
**Fully implemented with 200+ lines, configuration, documentation, and error handling.**

### Cloud AI Providers (20)
- `ai_providers/openai`
- `ai_providers/anthropic`
- `ai_providers/google`
- `ai_providers/microsoft`
- `ai_providers/meta`
- `ai_providers/cohere`
- `ai_providers/ai21`
- `ai_providers/mistral`
- `ai_providers/perplexity`
- `ai_providers/together`
- `ai_providers/anyscale`
- `ai_providers/replicate`
- `ai_providers/huggingface`
- `ai_providers/stability`
- `ai_providers/midjourney`
- `ai_providers/runway`
- `ai_providers/amazon_bedrock`
- `ai_providers/alibaba`
- `ai_providers/baidu`
- `ai_providers/yandex`

### Local Model Platforms (10)
- `local_models/ollama`
- `local_models/lm_studio`
- `local_models/gpt4all`
- `local_models/localai`
- `local_models/jan`
- `local_models/koboldai`
- `local_models/text_generation_webui`
- `local_models/llama.cpp`
- `local_models/vllm`
- `local_models/exllama`

## Tier 2 – Functional Skeletons (15 items)
**50–100 line implementations that run but still lack docs, tests, and polish.**

- `windows_integration/*` (File system, registry, service, process, window, event log, scheduler, PowerShell, WMI, COM automation)
- `monitoring/*` (system monitor, GPU monitor, performance profiler, resource manager, metrics collector)

## Tier 3 – Placeholders / Backlog
**Stubs or generated code that still need true functionality.**

- `code_models/*` (15)
- `vision_models/*` (20)
- `audio_models/*` (25)
- `logging/*` (compliance, aggregator, analyzer, archiver, shipper, alert manager are being added now)
- `developer_tools/*` (10)
- `marketplace/*`, `sdk/*`, and the majority of remaining plugin namespaces

## How to Update
1. Only move a plugin “up” a tier after adding real functionality plus config, README, and tests.
2. Whenever a plugin graduates to Tier 1, update this file **and**
   `PROGRESS_TRACKER.md`.
3. Keep plugin READMEs honest—note if something is experimental or incomplete.

Maintaining this index prevents the roadmap from drifting and keeps every
contributor aligned on what “done” actually means.
