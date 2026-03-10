# Windows AI — Master Blueprint

**Version:** 2.1 (March 2026)  
**Single Source of Truth** — Supersedes `docs/WindowsAI_Master_Blueprint.md`, `docs/WindowsAI_Blueprint_Index.md`, and all previous blueprint versions.

> **⚠️ MANDATORY FOR ALL AI AGENTS:** Every agent session (Claude, Copilot, or any other AI assistant) **MUST** read this file and `ROADMAP.md` before starting any development work. This blueprint defines the system architecture, directory structure, and component contracts. See the Enforcement section at the bottom of this file.

---

## 🎯 Purpose

Windows AI is a **locally-runnable, privacy-respecting AI platform for Windows** that:
- Provides 2,000+ AI capabilities through a single unified Python API
- Runs fully offline with local models (Ollama, LM Studio, llama.cpp)
- Connects to cloud AI (OpenAI, Anthropic, Google, Mistral, etc.) when desired
- Exposes a desktop GUI, REST API, CLI, and plugin SDK
- Orchestrates AI agents, workflows, IoT devices, and OS automation

**Philosophy:** *Freedom First* — all restrictive features are **OFF** by default. Users opt in.

---

## 🏗️ System Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                      USER INTERFACES                             ║
║  Electron GUI (apps/gui/)  │  REST API  │  CLI  │  Python SDK   ║
╚══════════════════════════╤═══════════════════════════════════════╝
                           ↓
╔══════════════════════════════════════════════════════════════════╗
║                  ORCHESTRATION LAYER                             ║
║         WindowsAI class (windows_ai/core/orchestrator.py)       ║
║   Auto-Setup · Plugin Manager · Credential Manager · Config     ║
╚══════════════════════════╤═══════════════════════════════════════╝
                           ↓
╔══════════════════════════════════════════════════════════════════╗
║                   INTEGRATION LAYER                              ║
║         51 Specialized Managers (windows_ai/integrations/)      ║
║  AI Providers · Image Gen · Audio/Speech · Video · Documents    ║
║  Browser Automation · Databases · Cloud Storage · Monitoring    ║
║  Agents · RAG Pipeline · Vector Stores · Workflows · Email      ║
╚══════════════════════════╤═══════════════════════════════════════╝
                           ↓
╔══════════════════════════════════════════════════════════════════╗
║                     PLUGIN LAYER                                 ║
║          2,203 plugins in windows_ai/plugins/builtin/           ║
║  windows/  windows_os/  audio_models/  vision_models/           ║
║  code_models/  cloud/  creative/  finance/  gaming/  ...        ║
╚══════════════════════════╤═══════════════════════════════════════╝
                           ↓
╔══════════════════════════════════════════════════════════════════╗
║                   FRAMEWORK LAYER                                ║
║  UnifiedLLM · LangChain · LlamaIndex · LiteLLM · HuggingFace   ║
║  RAG Pipeline · Vector DBs · Embeddings · Agent Coordination    ║
╚══════════════════════════╤═══════════════════════════════════════╝
                           ↓
╔══════════════════════════════════════════════════════════════════╗
║                  SYSTEM RESOURCES                                ║
║    Windows OS · File System · GPU/CPU/RAM · Network · Hardware  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 📦 Repository Structure

```
Windows-AI/
│
├── ROADMAP.md                    ← Single roadmap (this project's future)
├── BLUEPRINT.md                  ← This file (architecture truth)
├── README.md                     ← User-facing intro
├── CHANGELOG.md                  ← Version history
├── CLAUDE.md                     ← AI assistant dev guide
├── CONTRIBUTING.md               ← Contribution guidelines
├── SECURITY.md                   ← Security policy
├── LICENSE
├── setup.py                      ← Python package setup
├── requirements.txt              ← Core dependencies
├── requirements-dev.txt          ← Dev/test dependencies
├── pytest.ini                    ← Test configuration
├── package.json                  ← Node.js workspace root
├── Dockerfile                    ← Container build
├── docker-compose.yml
│
├── windows_ai/                   ← MAIN PYTHON PACKAGE
│   ├── __init__.py
│   ├── __main__.py               ← CLI entry point
│   ├── app.py                    ← FastAPI app factory
│   ├── main.py                   ← Full application (all routes)
│   ├── cli.py                    ← Command-line interface
│   │
│   ├── core/                     ← Core orchestration
│   │   ├── orchestrator.py       ← WindowsAI master class
│   │   ├── plugin_manager.py     ← Plugin lifecycle
│   │   ├── credential_manager.py ← Secure credential storage
│   │   ├── auto_setup.py         ← Zero-config initialization
│   │   ├── error_handling.py     ← Structured error handling
│   │   └── ...
│   │
│   ├── api/                      ← REST API layer
│   │   ├── server.py             ← FastAPI app + middleware
│   │   ├── routes.py             ← Plugin management endpoints
│   │   ├── chat_routes.py        ← Chat + streaming endpoints
│   │   ├── setup_routes.py       ← First-run wizard API
│   │   ├── credentials_routes.py ← Credential CRUD API
│   │   └── ...
│   │
│   ├── integrations/             ← 51 AI/service manager files
│   │   ├── __init__.py           ← Registry + initialize_integrations()
│   │   ├── ai_providers.py       ← OpenAI, Anthropic, Google, Groq…
│   │   ├── audio_speech.py       ← Whisper, ElevenLabs, Azure TTS…
│   │   ├── image_generation.py   ← DALL-E, Stable Diffusion, Midjourney…
│   │   └── ... (51 files total)
│   │
│   ├── plugins/                  ← Plugin system
│   │   ├── base.py               ← Plugin, PluginMetadata, PluginType
│   │   ├── registry.py           ← Plugin registry
│   │   ├── loader.py             ← Dynamic plugin loading
│   │   └── builtin/              ← 2,203 built-in plugins across 27 categories
│   │       ├── windows/          ← 51 Windows automation plugins
│   │       ├── windows_os/       ← 31 Windows OS management plugins
│   │       ├── audio_models/     ← 29 audio AI plugins (300–650 lines each)
│   │       ├── vision_models/    ← 21 vision AI plugins (150–320 lines each)
│   │       ├── code_models/      ← 16 code AI plugins (296–416 lines each)
│   │       ├── cloud/            ← Cloud service plugins
│   │       ├── creative/         ← Creative AI plugins
│   │       ├── finance/          ← Finance AI plugins
│   │       └── ...
│   │
│   ├── agents/                   ← Multi-agent system
│   ├── rag/                      ← RAG pipeline (retrieval, chunking, re-rank)
│   ├── vector_db/                ← ChromaDB, Faiss, Pinecone, Qdrant, Weaviate
│   ├── search/                   ← Search service (29 files, 10,007 lines — local + remote + semantic)
│   ├── security/                 ← Sandbox, audit, permissions, encryption
│   ├── frameworks/               ← UnifiedLLM, LangChain, LlamaIndex wrappers
│   ├── optimization/             ← Hardware profiling + tuning profiles
│   ├── config/                   ← Unified configuration (WindowsAIConfig)
│   ├── cloud_sync/               ← Cloud synchronization + encryption
│   ├── workflow/                 ← Workflow automation engine
│   ├── terminal/                 ← Terminal integration
│   ├── snapshot/                 ← System snapshot capabilities
│   ├── rollback/                 ← State rollback
│   ├── updater/                  ← Auto-update system
│   ├── database/                 ← Database abstractions
│   ├── monitoring/               ← Metrics + logging
│   ├── mesh/                     ← Mesh network coordination
│   ├── iot/                      ← IoT hardware integration
│   └── gui/                      ← GUI utilities (not the Electron app)
│
├── apps/                         ← Application layer
│   ├── gui/                      ← Electron desktop application
│   │   ├── main.js               ← Main process
│   │   ├── preload.js            ← IPC security bridge
│   │   ├── updater.js            ← Auto-update logic
│   │   ├── renderer/             ← HTML/CSS/JS frontend
│   │   └── electron-builder.yml  ← Installer config
│   ├── actions/                  ← Actions API (Node.js)
│   ├── agenthub/                 ← AgentHub (FastAPI)
│   └── proxy/                    ← Model proxy
│
├── xr/                           ← XR/AR/VR support
│   ├── __init__.py               ← load_runtime(), load_spatial_ui()
│   ├── runtime.py                ← RuntimeManager (OpenXR/WebXR detection)
│   ├── input_manager.py          ← XRInputManager (controllers, hands, eyes)
│   └── spatial_ui/               ← Spatial UI panels + GestureVoiceController
│
├── iot/                          ← IoT device management (37 files — MQTT, Matter, Zigbee, HA, Tuya, Ring, Nest, Hue…)
│   ├── models.py                 ← Device, DeviceAdapter base classes
│   ├── mqtt.py                   ← MQTT protocol adapter
│   ├── matter.py                 ← Matter protocol adapter
│   ├── zigbee.py                 ← Zigbee adapter
│   ├── home_assistant.py         ← Home Assistant integration
│   ├── automation.py             ← WorkflowAutomation
│   ├── adapters/                 ← Device-specific adapters (Arduino, ESP, Ring, Tuya, TP-Link, Sonos…)
│   ├── device_actions/           ← Device action handlers
│   └── hubs/                     ← Hub integrations
│
├── optimization/                 ← Hardware optimization (14 files — profiling, tuning, telemetry, sentinel, guardian)
│   ├── profiling.py              ← profile_hardware() using psutil/stdlib (334 lines)
│   ├── tuning.py                 ← Tuner, PROFILES (balanced/performance/eco)
│   └── optimization_*.py         ← Telemetry, scanner, guardian, companion, workflow, etc.
│
├── tests/                        ← Test suite (253 test files)
│   ├── unit/                     ← Unit tests
│   ├── integration/              ← Integration tests
│   ├── e2e/                      ← End-to-end tests
│   └── security/                 ← Security-specific tests
│
├── docs/                         ← All documentation
│   ├── api/                      ← API reference docs
│   ├── planning/                 ← Historical planning docs
│   ├── architecture/             ← Architecture decision records
│   ├── archive/roadmaps/         ← All old roadmap files (do not edit)
│   └── ...
│
├── scripts/                      ← Automation scripts
│   ├── build/                    ← Build scripts (PyInstaller, electron-builder)
│   ├── entry/                    ← Start scripts (start-backend.sh, etc.)
│   └── utilities/                ← Utility scripts
│
└── config/                       ← Configuration templates
```

---

## 🔌 Plugin Architecture

### Plugin Base Classes

```python
# All plugins inherit from one of these:
class Plugin(ABC):                    # Base for all plugins
class IntegrationPlugin(Plugin):      # For external service integrations
class ActionPlugin(Plugin):           # For one-shot actions
class ToolPlugin(Plugin):             # For reusable tools
class AutomationPlugin(Plugin):       # For OS automation

# Every plugin must implement:
async def initialize(self) -> bool
async def execute(self, action: str, parameters: dict, **kwargs) -> dict
async def shutdown(self) -> None
def get_schema(self) -> dict

# Every plugin file ends with:
plugin = MyPlugin()                   # singleton instance
```

### Plugin Types

| Type | Count | Location | Purpose |
|---|---|---|---|
| Windows Automation | 51 | `builtin/windows/` | Windows OS automation (registry, firewall, RDP…) |
| Windows OS Management | 31 | `builtin/windows_os/` | VSS, AD, Hyper-V, WinGet, WSL2… |
| Audio AI | 29 | `builtin/audio_models/` | Whisper, Vosk, Azure Speech, ElevenLabs… (300–650 lines each) |
| Vision AI | 21 | `builtin/vision_models/` | CLIP, BLIP2, DINO, Florence2, Grounding DINO… (150–320 lines each) |
| Code AI | 16 | `builtin/code_models/` | GitHub Copilot, CodeWhisperer, Tabnine… (296–416 lines each) |
| Cloud Services | ~50 | `builtin/cloud/` | AWS, Azure, GCP integrations |
| Creative AI | ~40 | `builtin/creative/` | Image/video/music generation |
| Finance AI | ~30 | `builtin/finance/` | Market data, trading, analysis |
| Generated/Other | ~1900+ | Various | Community + generated plugins |

---

## 🤖 Integration Managers (51 files)

Each manager in `windows_ai/integrations/` follows the same pattern:

```python
class MyManager:
    def __init__(self, config: WindowsAIConfig): ...
    async def initialize(self) -> bool: ...
    async def cleanup(self) -> None: ...
    # domain methods...
```

| Manager | Key Services |
|---|---|
| `AIProvidersManager` | OpenAI, Anthropic, Google, Mistral, Cohere, Groq |
| `ImageGenerationManager` | DALL-E 3, Midjourney, Stable Diffusion, Leonardo |
| `AudioSpeechManager` | Whisper, ElevenLabs, Azure Speech, Google TTS |
| `VideoGenerationManager` | RunwayML, Synthesia, Pika |
| `DocumentProcessingManager` | PDF, OCR, Word, Excel |
| `WindowsAutomationManager` | Windows-specific OS automation |
| `BrowserAutomationManager` | Playwright, Selenium, Puppeteer |
| `DatabaseManager` | PostgreSQL, MongoDB, Redis, MySQL, SQLite |
| `CloudStorageManager` | AWS S3, Azure Blob, Google Cloud Storage |
| `EmbeddingsManager` | OpenAI, Cohere, local sentence-transformers |
| `VectorStoresManager` | Pinecone, Weaviate, Qdrant, ChromaDB |
| `RAGPipelineManager` | Full RAG orchestration |
| `AIAgentsManager` | Multi-agent task coordination |
| … | (51 files — see `integrations/__init__.py` and directory listing) |

---

## 🌐 API Endpoints

**Base URL:** `http://127.0.0.1:8010`

| Method | Path | Description |
|---|---|---|
| GET | `/health` | System health check |
| POST | `/chat` | Chat with AI |
| GET | `/chat/stream` | Streaming chat (SSE) |
| GET | `/plugins` | List all plugins |
| GET | `/plugins/{id}` | Plugin details |
| POST | `/plugins/{id}/execute` | Execute plugin |
| GET | `/models` | Available AI models |
| GET | `/integrations/status` | Integration manager status |
| GET | `/conversations` | Chat history |
| GET `/POST /DELETE` | `/credentials` | Credential management |
| POST | `/setup/*` | First-run wizard |
| GET | `/rag/*` | RAG pipeline endpoints |

---

## 🔧 Configuration

Windows AI uses a unified `WindowsAIConfig` (Pydantic-based):

```python
from windows_ai.config.unified_config import get_config
config = get_config()          # auto-discovers config files
config.server.port             # 8010 by default
config.llm.provider            # "openai" by default
config.llm.api_key             # from env OPENAI_API_KEY
```

**Config file search order:**
1. Path passed to `get_config(path=...)`
2. `data/config.json` or `data/config.yaml`
3. `windows_ai/config/default.yaml`
4. Built-in defaults

**Environment overrides:**
```bash
WINDOWSAI_SERVER__PORT=8080
WINDOWSAI_LLM__PROVIDER=anthropic
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 🏃 Running the Application

```bash
# Backend (Python API server)
python -m windows_ai                        # Launch with GUI
python -m uvicorn windows_ai.api.server:app --reload --port 8010

# Desktop GUI (Electron)
cd apps/gui && npm install && npm start

# CLI
python -m windows_ai interactive            # Interactive mode
python -m windows_ai chat "Hello, AI"       # Single message
python -m windows_ai status                 # System status

# Build
python build_exe.py                         # PyInstaller executable
cd apps/gui && npm run build:win            # Windows installer
```

---

## 🧪 Testing

```bash
pytest tests/unit/ -q                       # All unit tests
pytest -m unit                             # Unit tests only
pytest -m integration                      # Integration tests
pytest -m critical                         # Critical path only
pytest tests/unit/test_quick_wins.py       # 11 quick-win tests
pytest --cov=windows_ai                    # With coverage
```

**Test markers:** `unit`, `integration`, `e2e`, `slow`, `critical`, `security`

---

## 🔒 Security Design

**"Freedom First" philosophy:**
- All restrictive security features are **OFF** by default
- Users explicitly opt in to security controls
- No data collection without consent
- Local-first: data never leaves the device unless user chooses cloud

**Security layers:**
1. **Credential Manager** — encrypted storage (NaCl or XOR fallback)
2. **Sandbox** — file/network/process restrictions (NONE → MAXIMUM levels)
3. **Plugin isolation** — plugins run in restricted execution contexts
4. **API security** — optional API key authentication, rate limiting
5. **Audit logging** — optional audit trail of all privileged operations

---

## 🚀 Model Support

### Cloud Providers (API key required)
- OpenAI: GPT-4o, GPT-4, GPT-3.5-turbo, o1, o3
- Anthropic: Claude 3 Opus/Sonnet/Haiku, Claude 3.5
- Google: Gemini 1.5 Pro/Flash, Gemini 2.0
- Mistral: Mistral Large/Medium/Small
- Cohere: Command R+, Command R
- Groq: LLaMA 3, Mixtral (fast inference)

### Local Models (no API key)
- Ollama (port 11434): Any GGUF model
- LM Studio (port 1234): Any GGUF model
- text-generation-webui (port 5000): transformers models
- vLLM (port 8000): GPU-accelerated inference
- llama.cpp direct: CPU/GPU inference

---

## 📊 Dependency Map

```
windows_ai (core)
  ├── fastapi + uvicorn         → REST API server
  ├── pydantic                  → Config + data validation
  ├── openai                    → OpenAI API
  ├── anthropic                 → Anthropic API
  ├── google-generativeai       → Google Gemini
  ├── litellm                   → Unified LLM proxy
  ├── langchain                 → LLM orchestration framework
  ├── llama-index               → RAG + document processing
  ├── chromadb                  → Local vector database
  ├── sentence-transformers     → Local embeddings
  ├── aiohttp + httpx           → Async HTTP clients
  ├── pynacl                    → Encryption (optional, XOR fallback)
  ├── pandas + numpy            → Data processing
  └── psutil                    → System monitoring

apps/gui (Electron)
  ├── electron                  → Desktop app framework
  ├── electron-builder          → Installer creation
  ├── marked.js                 → Markdown rendering
  └── highlight.js              → Syntax highlighting
```

---

## 🗂️ Archived Documents

The following files are kept for historical reference only. **Do not update them** — update this BLUEPRINT.md and ROADMAP.md instead.

```
docs/archive/roadmaps/
  ├── ROADMAP_MASTER.md          (was docs/master_plan/ROADMAP_MASTER.md)
  ├── MASTER_ROADMAP_CONSOLIDATED.md
  ├── ROADMAP_ARCHIVAL_REPORT.md
  ├── TODO_MASTER_historical.md
  └── deprecated/
      ├── ROADMAP.md
      └── ROADMAP_CONSOLIDATION_SUMMARY.md
```

---

## 🛡️ Enforcement — Agent Compliance

> **This section is MANDATORY for all AI agents working on this repository.**

1. **Read before coding.** Every agent session must read `BLUEPRINT.md` (this file) and `ROADMAP.md` before making changes. These define the architecture and development plan.

2. **Follow the architecture.** All new code must fit within the layered architecture described above. Do not create parallel systems or competing module hierarchies.

3. **Use correct paths.** Plugin directories are at `windows_ai/plugins/builtin/{category}/`. The correct categories include: `audio_models/`, `vision_models/`, `code_models/`, `windows/`, `windows_os/`, etc. There are no directories named `windows_ai/plugins/audio_ai/`, `vision_ai/`, or `code_ai/`.

4. **Update on changes.** When adding new modules, directories, or major features, update this file's repository structure section.

5. **No contradictions.** If `CLAUDE.md`, `.github/copilot-instructions.md`, or `docs/planning/TODO_MASTER.md` contradicts this blueprint, **this blueprint takes precedence**. Update the conflicting file.

6. **Cross-references.** This enforcement is also declared in `ROADMAP.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`.

---

*This is the single authoritative architecture blueprint for Windows AI.*  
*For planned features and milestones, see [ROADMAP.md](./ROADMAP.md).*
