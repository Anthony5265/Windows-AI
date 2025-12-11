# AI Models & Frameworks Catalog

## Top 50 AI Models

| Model Name | Provider | Type | Access | GPU Required | Integration Status |
|------------|----------|------|--------|--------------|-------------------|
| GPT-4 Turbo | OpenAI | LLM | API | No | Planned |
| GPT-4o | OpenAI | Multimodal | API | No | Planned |
| GPT-3.5 Turbo | OpenAI | LLM | API | No | Planned |
| Claude 3.5 Sonnet | Anthropic | LLM | API | No | Planned |
| Claude 3 Opus | Anthropic | LLM | API | No | Planned |
| Claude 3 Haiku | Anthropic | LLM | API | No | Planned |
| Gemini 1.5 Pro | Google | Multimodal | API | No | Planned |
| Gemini 1.5 Flash | Google | Multimodal | API | No | Planned |
| Gemini Ultra | Google | Multimodal | API | No | Planned |
| LLaMA 3.1 405B | Meta | LLM | Local/API | Yes | Planned |
| LLaMA 3.1 70B | Meta | LLM | Local/API | Yes | Planned |
| LLaMA 3.1 8B | Meta | LLM | Local/API | Optional | Planned |
| LLaMA 3.2 3B | Meta | LLM | Local | No | Planned |
| LLaMA 3.2 1B | Meta | LLM | Local | No | Planned |
| Mistral Large 2 | Mistral AI | LLM | API | No | Planned |
| Mistral 7B | Mistral AI | LLM | Local/API | Optional | Planned |
| Mixtral 8x7B | Mistral AI | LLM | Local/API | Yes | Planned |
| Mixtral 8x22B | Mistral AI | LLM | Local/API | Yes | Planned |
| Codestral | Mistral AI | Code | API | No | Planned |
| Code Llama 34B | Meta | Code | Local/API | Yes | Planned |
| Code Llama 13B | Meta | Code | Local/API | Optional | Planned |
| Code Llama 7B | Meta | Code | Local | No | Planned |
| StarCoder2 15B | BigCode | Code | Local/API | Optional | Planned |
| StarCoder2 7B | BigCode | Code | Local | No | Planned |
| Codex | OpenAI | Code | API | No | Planned |
| GPT-4 Vision | OpenAI | Vision | API | No | Planned |
| Gemini Vision Pro | Google | Vision | API | No | Planned |
| LLaVA 1.6 34B | LLaVA | Vision | Local | Yes | Planned |
| LLaVA 1.5 13B | LLaVA | Vision | Local | Optional | Planned |
| CLIP ViT-L/14 | OpenAI | Vision | Local | Optional | Planned |
| CLIP ViT-B/32 | OpenAI | Vision | Local | No | Planned |
| Whisper Large v3 | OpenAI | Audio | Local/API | Optional | Planned |
| Whisper Medium | OpenAI | Audio | Local | No | Planned |
| Whisper Small | OpenAI | Audio | Local | No | Planned |
| Azure Speech | Microsoft | Audio | API | No | Planned |
| Phi-3.5 Mini | Microsoft | LLM | Local | No | Planned |
| Phi-3.5 Medium | Microsoft | LLM | Local | Optional | Planned |
| Qwen2.5 72B | Alibaba | LLM | Local/API | Yes | Planned |
| Qwen2.5 14B | Alibaba | LLM | Local | Optional | Planned |
| Qwen2.5 7B | Alibaba | LLM | Local | No | Planned |
| DeepSeek Coder V2 | DeepSeek | Code | Local/API | Yes | Planned |
| Stable Diffusion XL | Stability AI | Image Gen | Local | Yes | Planned |
| DALL-E 3 | OpenAI | Image Gen | API | No | Planned |
| Flux.1 Dev | Black Forest Labs | Image Gen | Local | Yes | Planned |
| Llama Guard 3 | Meta | Safety | Local | No | Planned |
| Command R+ | Cohere | LLM | API | No | Planned |
| Command R | Cohere | LLM | API | No | Planned |
| Jamba 1.5 Large | AI21 | LLM | API | No | Planned |
| Falcon 180B | TII | LLM | Local/API | Yes | Planned |
| Yi-34B | 01.AI | LLM | Local/API | Yes | Planned |

## Top 30 Frameworks & Tools

| Tool Name | Category | Plugin Wrapper Needed | Config Location |
|-----------|----------|----------------------|-----------------|
| Ollama | Runtime | Yes | `config/providers/ollama.yaml` |
| LM Studio | Runtime | Yes | `config/providers/lmstudio.yaml` |
| GPT4All | Runtime | Yes | `config/providers/gpt4all.yaml` |
| PyTorch | Framework | No | `config/frameworks/pytorch.yaml` |
| TensorFlow | Framework | No | `config/frameworks/tensorflow.yaml` |
| ONNX Runtime | Framework | No | `config/frameworks/onnx.yaml` |
| Transformers (HF) | Library | Yes | `config/libraries/transformers.yaml` |
| LangChain | Orchestration | Yes | `config/orchestration/langchain.yaml` |
| LlamaIndex | Orchestration | Yes | `config/orchestration/llamaindex.yaml` |
| AutoGen | Multi-Agent | Yes | `config/orchestration/autogen.yaml` |
| CrewAI | Multi-Agent | Yes | `config/orchestration/crewai.yaml` |
| Haystack | Orchestration | Yes | `config/orchestration/haystack.yaml` |
| vLLM | Inference | Yes | `config/inference/vllm.yaml` |
| Text Generation WebUI | Interface | Yes | `config/interfaces/textgen.yaml` |
| Kobold AI | Interface | Yes | `config/interfaces/kobold.yaml` |
| LocalAI | Runtime | Yes | `config/providers/localai.yaml` |
| Jan | Runtime | Yes | `config/providers/jan.yaml` |
| Llama.cpp | Runtime | Yes | `config/runtimes/llamacpp.yaml` |
| OpenAI Python SDK | API Client | Yes | `config/sdks/openai.yaml` |
| Anthropic Python SDK | API Client | Yes | `config/sdks/anthropic.yaml` |
| Google AI SDK | API Client | Yes | `config/sdks/google.yaml` |
| Azure OpenAI SDK | API Client | Yes | `config/sdks/azure_openai.yaml` |
| Docker | Deployment | No | `config/deployment/docker.yaml` |
| venv | Environment | No | `config/deployment/venv.yaml` |
| conda | Environment | No | `config/deployment/conda.yaml` |
| Gradio | UI Framework | Yes | `config/ui/gradio.yaml` |
| Streamlit | UI Framework | Yes | `config/ui/streamlit.yaml` |
| FastAPI | API Framework | No | `config/api/fastapi.yaml` |
| Chainlit | Chat UI | Yes | `config/ui/chainlit.yaml` |
| Semantic Kernel | Orchestration | Yes | `config/orchestration/semantic_kernel.yaml` |

## Implementation Strategy

### Plugin Stub Design
- **Adapter Pattern**: Each external tool gets a thin adapter class in `windows_ai/plugins/adapters/`
- **Lazy Loading**: Plugins initialize only when requested via config
- **Fallback Chain**: If primary provider fails, fallback to alternatives defined in config
- **Stub Interface**: Common interface (`BaseModelProvider`, `BaseRuntime`) for all adapters
- **Version Detection**: Auto-detect installed tool versions and capabilities

### Config Schema Structure
```yaml
# config/providers/{provider_name}.yaml
provider:
  name: "ollama"
  type: "local_runtime"
  enabled: true
  priority: 10
  
connection:
  host: "localhost"
  port: 11434
  api_base: "http://localhost:11434"
  
models:
  - name: "llama3.1:8b"
    type: "llm"
    context_window: 128000
    
capabilities:
  streaming: true
  embeddings: true
  function_calling: false
  
requirements:
  min_ram_gb: 8
  gpu_optional: true
```

### Provider Registry Pattern
- **Central Registry**: `windows_ai/core/provider_registry.py` tracks all available providers
- **Dynamic Discovery**: Scan `config/providers/` on startup to build registry
- **Capability Matching**: Query registry by capability (e.g., "streaming LLM with <16GB RAM")
- **Health Checks**: Periodic ping to verify provider availability
- **Failover Logic**: Automatic switch to backup provider on failure
- **Usage Metrics**: Track calls, tokens, latency per provider for optimization

### Integration Phases
1. **Phase 1**: Implement registry + 3 core adapters (Ollama, OpenAI API, Azure OpenAI)
2. **Phase 2**: Add local model runners (LM Studio, GPT4All, llama.cpp)
3. **Phase 3**: Integrate orchestration frameworks (LangChain, LlamaIndex)
4. **Phase 4**: Add specialized tools (Whisper, CLIP, Stable Diffusion)
5. **Phase 5**: Multi-agent frameworks (AutoGen, CrewAI)
