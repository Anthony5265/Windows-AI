# Windows AI - AI Agent Development Instructions

## 🤖 CRITICAL RULE #0 - SUBAGENT AWARENESS & AUTO-DELEGATION ⚠️

**YOU HAVE 78 SPECIALIZED SUBAGENTS AT YOUR DISPOSAL - USE THEM AUTOMATICALLY!**

### 🚨 MANDATORY SUBAGENT DELEGATION PROTOCOL 🚨

**For EVERY task you receive, you MUST:**

1. ✅ **IMMEDIATELY ASSESS** if a specialized subagent would be better suited
2. ✅ **AUTOMATICALLY DELEGATE** complex tasks to the appropriate subagent using `runSubagent` tool
3. ✅ **USE MULTIPLE SUBAGENTS** in parallel when tasks have independent components
4. ✅ **ALWAYS CONSIDER** subagent delegation BEFORE attempting tasks yourself

### When to Auto-Delegate to Subagents:

**System Design/Architecture** → `runSubagent({agentName: "Architect", ...})`
**Code Generation** → `runSubagent({agentName: "CodeGenerator", ...})`
**Performance Issues** → `runSubagent({agentName: "PerformanceOptimizer", ...})`
**API Design** → `runSubagent({agentName: "APIDesigner", ...})`
**Database Work** → `runSubagent({agentName: "DatabaseExpert", ...})`
**Documentation** → `runSubagent({agentName: "TechnicalWriter", ...})`
**Debugging** → `runSubagent({agentName: "Debugger", ...})`
**Refactoring** → `runSubagent({agentName: "Refactor", ...})`
**And 74 more specialists available!**

### Subagent Decision Matrix:

```
RECEIVE TASK
    ↓
IS IT COMPLEX/SPECIALIZED? ────YES──→ DELEGATE TO SUBAGENT(S)
    │                                        ↓
    NO                              CHOOSE BEST AGENT(S)
    ↓                                        ↓
DO IT YOURSELF                      USE runSubagent TOOL
```

**Remember: Subagents are EXPERTS in their domains. They will complete tasks faster and better than general processing. USE THEM!**

---

## ⚠️ CRITICAL RULE #1 - CONTINUOUS EXECUTION MANDATE ⚠️

**THIS IS THE MOST IMPORTANT RULE - READ THIS FIRST BEFORE ANYTHING ELSE**

### 🚨 ABSOLUTE REQUIREMENT: NEVER STOP UNTIL 100% COMPLETE 🚨

When developing Windows AI, you MUST follow this non-negotiable rule:

**ONCE YOU START A DEVELOPMENT TASK, YOU DO NOT STOP UNTIL IT IS 100% COMPLETE. NO EXCEPTIONS.**

This means:

1. ❌ **DO NOT** stop after reading files
2. ❌ **DO NOT** stop after analyzing the codebase
3. ❌ **DO NOT** stop after creating a plan
4. ❌ **DO NOT** stop after implementing one component
5. ❌ **DO NOT** stop after fixing one issue
6. ❌ **DO NOT** stop after updating documentation
7. ❌ **DO NOT** ask "should I continue?" - THE ANSWER IS ALWAYS YES
8. ❌ **DO NOT** wait for feedback mid-task - KEEP GOING
9. ❌ **DO NOT** stop because you think you've done "enough" - FINISH EVERYTHING

### ✅ WHAT YOU MUST DO INSTEAD:

1. ✅ **CREATE A COMPREHENSIVE TASK LIST** using `manage_todo_list` tool
2. ✅ **MARK EACH TASK IN-PROGRESS** before starting it
3. ✅ **COMPLETE THE ENTIRE TASK** before marking it done
4. ✅ **IMMEDIATELY START THE NEXT TASK** after finishing one
5. ✅ **CONTINUE THROUGH ALL TASKS** until every single one is complete
6. ✅ **VERIFY COMPLETION** - check builds, validate functionality
7. ✅ **ONLY STOP** when the todoList shows 100% completion status

### 📋 CONTINUOUS EXECUTION WORKFLOW:

```
START TASK
    ↓
READ/ANALYZE (quickly, don't over-analyze)
    ↓
CREATE TODO LIST with manage_todo_list
    ↓
FOR EACH TODO:
    ↓
    Mark as "in-progress"
    ↓
    IMPLEMENT FULLY (not partially)
    ↓
    Mark as "completed"
    ↓
    IMMEDIATELY START NEXT TODO
    ↓
REPEAT UNTIL ALL TODOS = "completed"
    ↓
VERIFY 100% COMPLETION
    ↓
ONLY THEN: END TASK
```

### 🎯 COMPLETION CRITERIA:

A task is NOT complete until:

- ✅ All code is implemented (no stubs, no TODOs, no placeholders)
- ✅ All integration points work correctly
- ✅ All documentation is updated
- ✅ Build system produces working artifacts
- ✅ All error handling is implemented
- ✅ All edge cases are covered
- ✅ Performance is optimized
- ✅ Everything is production-ready

### 🔥 EXAMPLES OF WHAT "CONTINUOUS EXECUTION" LOOKS LIKE:

**BAD (DO NOT DO THIS):**

```
Agent: "I've analyzed the codebase. It needs completion in several areas."
[STOPS HERE] ❌
```

**GOOD (DO THIS):**

```
Agent: "I've analyzed the codebase. Creating comprehensive completion plan..."
[Creates 50-item todo list]
Agent: "Starting Phase 1: Core System Implementation..."
[Implements 10 core files]
Agent: "Phase 1 complete. Starting Phase 2: Integration Layer..."
[Implements 15 integration files]
Agent: "Phase 2 complete. Starting Phase 3: Documentation..."
[Updates all docs]
Agent: "Phase 3 complete. Running final validation..."
[Runs all builds, checks]
Agent: "✅ ALL TASKS 100% COMPLETE. System is production-ready."
[ONLY NOW STOPS] ✅
```

### ⚡ EXECUTION SPEED REQUIREMENTS:

- Use `multi_replace_string_in_file` for batch edits (faster)
- Read multiple files in parallel when possible
- Don't re-read files unnecessarily
- Work systematically through components
- Maintain momentum - no long pauses between tasks
- Use efficient tools for each task type

### 🚫 FORBIDDEN BEHAVIORS:

These behaviors are STRICTLY PROHIBITED:

1. **"Analysis Paralysis"** - Don't spend hours analyzing. Read quickly, plan briefly, then EXECUTE.
2. **"Incremental Stopping"** - Don't stop after each small increment. Complete large chunks.
3. **"Permission Seeking"** - Don't ask "should I continue?" Just continue.
4. **"Premature Completion"** - Don't declare victory early. Verify 100% completion.
5. **"Scope Reduction"** - Don't reduce scope to finish faster. Complete the full scope.
6. **"Stub Implementation"** - Don't leave placeholders. Implement everything fully.
7. **"Documentation Deferral"** - Don't skip docs. Update them as you go.

### 📊 PROGRESS TRACKING REQUIREMENT:

You MUST use the `manage_todo_list` tool to track progress:

```python
# At start of task
manage_todo_list(todoList=[
    {"id": 1, "title": "Implement core orchestrator", "status": "not-started"},
    {"id": 2, "title": "Create integration managers", "status": "not-started"},
    {"id": 3, "title": "Build plugin system", "status": "not-started"},
    # ... all tasks
])

# When starting a task
manage_todo_list(todoList=[
    {"id": 1, "title": "Implement core orchestrator", "status": "in-progress"},
    # ... rest
])

# When completing a task
manage_todo_list(todoList=[
    {"id": 1, "title": "Implement core orchestrator", "status": "completed"},
    {"id": 2, "title": "Create integration managers", "status": "in-progress"},
    # ... rest
])

# Continue until ALL tasks show "completed"
```

### 🎓 REMEMBER:

> **"The task is not done until it's COMPLETELY done. No partial completions. No stopping mid-way. Execute continuously from start to 100% completion."**

If you find yourself wanting to stop before 100% completion, GO BACK TO THE TOP OF THIS SECTION AND RE-READ THE RULES.

---

## Project Architecture

Windows AI is a comprehensive AI platform providing 2500+ capabilities through a **Master Orchestrator pattern**. The `WindowsAI` class in `windows_ai/core/orchestrator.py` acts as the central entry point, coordinating 43 specialized managers (LLM, vision, audio, cloud, databases, etc.) that provide domain-specific functionality.

### Detailed Architecture Overview

The system is built on a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACES LAYER                        │
│  • Electron GUI (apps/gui/)                                     │
│  • CLI Interface (windows_ai/__main__.py)                       │
│  • REST API (windows_ai/api/)                                   │
│  • Python SDK (windows_ai/__init__.py)                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                            │
│  • WindowsAI Orchestrator (windows_ai/core/orchestrator.py)    │
│  • Plugin Manager (windows_ai/core/plugin_manager.py)           │
│  • Auto Setup (windows_ai/core/auto_setup.py)                   │
│  • Credential Manager (windows_ai/core/credential_manager.py)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                             │
│  43 Specialized Managers (windows_ai/integrations/):           │
│  • AIProvidersManager - OpenAI, Anthropic, Google, etc.        │
│  • ImageGenerationManager - DALL-E, Midjourney, Stable Diff.   │
│  • AudioSpeechManager - Whisper, ElevenLabs, Azure Speech      │
│  • VideoGenerationManager - RunwayML, Synthesia, etc.          │
│  • DocumentProcessingManager - PDF, OCR, document analysis     │
│  • WindowsAutomationManager - Windows-specific automation      │
│  • BrowserAutomationManager - Selenium, Playwright, Puppeteer │
│  • DatabaseManager - PostgreSQL, MongoDB, Redis, MySQL         │
│  • CloudStorageManager - AWS S3, Azure Blob, Google Cloud     │
│  • [35 more managers...]                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      PLUGIN LAYER                                │
│  • Base Plugin System (windows_ai/plugins/base.py)             │
│  • Plugin Registry (windows_ai/plugins/registry.py)            │
│  • Plugin Loader (windows_ai/plugins/loader.py)                │
│  • 200+ Built-in Plugins (windows_ai/plugins/builtin/)        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     FRAMEWORK LAYER                              │
│  • UnifiedLLM (windows_ai/frameworks/unified_llm.py)           │
│  • Vector Databases (windows_ai/vector_db/)                    │
│  • RAG Pipeline (windows_ai/rag/)                              │
│  • Agent Coordination (windows_ai/agents/)                     │
│  • Workflow Engine (windows_ai/workflow/)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   SYSTEM RESOURCES                               │
│  • Operating System APIs                                        │
│  • File System                                                  │
│  • Network                                                      │
│  • Hardware (GPU, CPU, Memory)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Design Principles

1. **Zero Configuration**

   - Auto-detect environment and dependencies
   - Smart defaults for all settings
   - Automatic installation of missing components
   - Environment variable detection for API keys
   - Fallback mechanisms for all features

2. **Graceful Degradation**

   - Never crash the entire system
   - Log errors but continue operation
   - Provide fallbacks for failed operations
   - Disable unavailable features without blocking others
   - User-friendly error messages

3. **Modular Managers**

   - Each manager is independent and self-contained
   - Lazy loading - managers initialize only when needed
   - Clear interfaces between managers
   - No circular dependencies
   - Easy to add new managers

4. **Production Ready**
   - No placeholder functions
   - No stub implementations
   - No TODO comments in production code
   - Full error handling everywhere
   - Comprehensive logging
   - Performance optimized

### Critical Architecture Files (READ THESE FIRST)

#### 1. `windows_ai/core/orchestrator.py` (300 lines)

**Purpose**: Master coordinator for all 2500+ capabilities
**Key Components**:

- `WindowsAI` class - Main entry point
- `initialize()` - Auto-setup and configuration
- `_init_all_managers()` - Initializes all 43 managers
- `_auto_configure()` - Environment detection
- `_detect_api_keys()` - Automatic API key discovery

**Critical Methods**:

```python
async def initialize(self, config: Optional[Dict] = None)
    # Called first, sets up entire system

async def chat(self, message: str, **kwargs) -> str
    # Main chat interface

async def generate_image(self, prompt: str, **kwargs) -> str
    # Image generation entry point

async def execute_plugin(self, plugin_id: str, **kwargs) -> Dict
    # Execute any plugin by ID
```

#### 2. `windows_ai/integrations/__init__.py` (641 lines)

**Purpose**: Registry of all 43 integration managers
**Structure**: Imports and exports all manager classes
**Pattern**: Each manager follows identical structure

**All 43 Managers**:

```python
AIProvidersManager          # OpenAI, Anthropic, Google, Mistral, Cohere, Groq
ImageGenerationManager      # DALL-E, Midjourney, Stable Diffusion, Leonardo
AudioSpeechManager          # Whisper, ElevenLabs, Azure Speech, Google TTS
VideoGenerationManager      # RunwayML, Synthesia, Pika, Gen-2
DocumentProcessingManager   # PDF parsing, OCR, document analysis
WindowsAutomationManager    # Windows-specific automation tasks
BrowserAutomationManager    # Web scraping, browser control
ProductivityManager         # Calendar, email, notes integration
DataAnalysisManager         # Pandas, NumPy, data visualization
CodeAssistantsManager       # GitHub Copilot, CodeWhisperer, Tabnine
TranslationManager          # DeepL, Google Translate, multilingual support
SearchEnginesManager        # Google, Bing, DuckDuckGo integration
KnowledgeGraphManager       # Neo4j, graph databases
ThreeDGenerationManager     # 3D model generation
MusicGenerationManager      # AI music composition
EmbeddingsManager           # Text embeddings, vector representations
VectorStoresManager         # Pinecone, Weaviate, Qdrant, ChromaDB
WorkflowAutomationManager   # Complex workflow orchestration
EmailServicesManager        # Gmail, Outlook, SMTP
NotificationsManager        # Slack, Discord, Teams, SMS
CloudStorageManager         # AWS S3, Azure Blob, Google Cloud Storage
DatabaseManager             # PostgreSQL, MongoDB, Redis, MySQL
MonitoringManager           # System monitoring, metrics, logging
AIAgentsManager             # Multi-agent coordination
ContentModerationManager    # Content filtering, moderation
RAGPipelineManager          # Retrieval-Augmented Generation
MLOpsManager                # Model training, deployment, monitoring
PaymentsManager             # Stripe, PayPal integration
SocialMediaManager          # Twitter, Facebook, LinkedIn APIs
SchedulingManager           # Calendly, scheduling automation
CRMManager                  # Salesforce, HubSpot integration
IoTHardwareManager          # IoT device control
ComputerVisionManager       # Object detection, face recognition
HealthcareAIManager         # Medical AI applications
LegalAIManager              # Legal document processing
EducationAIManager          # Educational AI tools
FinanceAIManager            # Financial analysis, trading
ScientificAIManager         # Scientific computing
AccessibilityAIManager      # Accessibility features
RealEstateAIManager         # Property analysis
GamingAIManager             # Game AI integration
ConversationalAIManager     # Advanced dialogue systems
AutomationRoboticsManager   # Robotics control
BiometricsIdentityManager   # Biometric authentication
```

#### 3. `windows_ai/plugins/base.py` (323 lines)

**Purpose**: Foundation for all plugins
**Key Classes**:

- `Plugin` - Base class all plugins inherit from
- `PluginMetadata` - Plugin information and configuration
- `PluginType` - Enum of plugin types

**Plugin Lifecycle**:

```python
1. __init__() - Create plugin with metadata
2. initialize() - Setup resources (called once)
3. execute() - Main functionality (called many times)
4. cleanup() - Release resources (called on shutdown)
```

#### 4. `windows_ai/api/server.py` (349 lines)

**Purpose**: FastAPI REST API server
**Endpoints**:

- `/health` - Health check
- `/chat` - Text chat
- `/chat/stream` - Streaming chat
- `/plugins` - List plugins
- `/plugins/{id}` - Get plugin details
- `/plugins/{id}/execute` - Execute plugin
- `/models` - List available models
- `/conversations` - Conversation history
- `/setup/*` - Setup wizard endpoints
- `/credentials/*` - Credential management

### Key Architecture Files

- `windows_ai/core/orchestrator.py` - Master orchestrator coordinating all managers
- `windows_ai/integrations/__init__.py` - Registry of 43+ integration managers
- `windows_ai/plugins/base.py` - Plugin architecture with PluginType enum
- `windows_ai/api/server.py` - FastAPI REST API with all endpoints

## Development Workflow

### Building & Running

**Backend (Python)**

```bash
python build_exe.py              # Build PyInstaller executable
python -m windows_ai             # Launch GUI mode
python -m windows_ai interactive # CLI interactive mode
python -m windows_ai chat "msg"  # Direct chat
```

**GUI (Electron)**

```bash
cd apps/gui
npm install
npm run build        # Production build
npm run build:win    # Windows installer (NSIS)
```

**Quick Portable Build**

```bash
build-simple.bat     # Build both backend + GUI (Windows)
```

**Start Backend for Development**

```bash
python -m uvicorn windows_ai.api.server:app --reload --port 8010
# Or use test_backend.py for quick validation
```

## Plugin Development Pattern

Windows AI uses a standardized plugin architecture. All plugins inherit from `Plugin` base class:

```python
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType

class MyPlugin(Plugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="my-plugin",
            name="My Plugin",
            description="Does something useful",
            version="1.0.0",
            author="Your Name",
            plugin_type=PluginType.INTEGRATION  # or ACTION, TOOL, UI, AUTOMATION
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        """Initialize plugin resources"""
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main plugin logic"""
        return {"status": "success"}
```

**Plugin Types**: `ACTION`, `TOOL`, `INTEGRATION`, `UI`, `AUTOMATION`

Plugins are registered in `windows_ai/plugins/registry.py` and loaded by `PluginManager`.

## Manager Integration Pattern

Managers in `windows_ai/integrations/` follow a consistent pattern:

1. **Class name**: `{Domain}Manager` (e.g., `ImageGenerationManager`)
2. **Methods**: Async methods for all operations
3. **Error handling**: Graceful degradation with logging
4. **Registration**: Imported in `windows_ai/integrations/__init__.py`
5. **Initialization**: Called by orchestrator in `_init_all_managers()`

Example structure:

```python
class ImageGenerationManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False

    async def initialize(self):
        """Setup resources"""
        self._initialized = True

    async def generate_image(self, prompt: str, **kwargs):
        """Generate image from prompt"""
        # Implementation
```

## API Development

FastAPI routes are organized in `windows_ai/api/`:

- `server.py` - Main FastAPI app setup, middleware, docs
- `routes.py` - Core plugin management endpoints
- `chat_routes.py` - Chat and streaming endpoints
- `setup_routes.py` - Setup wizard endpoints
- `credentials_routes.py` - Credential management
- `frontend_routes.py` - Frontend serving

**Credentials**: Loaded from secure storage via `CredentialManager` on startup. See `load_credentials_to_env()` in `server.py`.

## Build System & Distribution

### PyInstaller Configuration

`build_exe.py` bundles the Python backend with extensive hidden imports for:

- Web frameworks: FastAPI, uvicorn, starlette
- AI providers: OpenAI, Anthropic, Google, Cohere, Mistral, Groq
- Vector DBs: ChromaDB, Faiss, Pinecone, Qdrant, Weaviate
- AI frameworks: LangChain, LlamaIndex, LiteLLM

**Spec file**: `WindowsAI.spec` (auto-generated, can be customized)

### Electron Build

`apps/gui/main.js` manages backend process lifecycle:

- Production: Backend bundled in `resources/backend/WindowsAI.exe`
- Development: Checks for existing backend on port 8010, falls back to `dist/WindowsAI/WindowsAI.exe`

**Windows Defender note**: electron-builder may be blocked. Add exclusions or use `build-simple.bat`.

## Common Patterns

### Async Everywhere

All I/O operations use async/await:

```python
async def my_function():
    result = await manager.do_something()
```

### Auto-Configuration

Detect API keys from environment on startup:

```python
key_patterns = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", ...]
detected = {k: os.environ.get(k) for k in key_patterns if os.environ.get(k)}
```

### Graceful Error Handling

Never crash—log and continue:

```python
try:
    await risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return default_value
```

## GUI Architecture (Electron)

Located in `apps/gui/`:

- `main.js` - Electron main process, backend management, IPC
- `preload.js` - Secure IPC bridge to renderer
- `renderer/` - Frontend UI (HTML/CSS/JS)
- `build/` - Build resources (icons, installers)

**Backend communication**: GUI connects to backend REST API on `http://127.0.0.1:8010`

## Contributing Checklist

Before submitting PRs:

- [ ] Code linted (`ruff check .` if applicable)
- [ ] Type hints added (`mypy windows_ai/`)
- [ ] Documentation updated (docstrings, README if needed)
- [ ] CHANGELOG.md updated

## Project Structure Reference

```
windows_ai/
├── core/           # Core orchestrator, plugin manager, auto-setup
├── integrations/   # 43+ specialized managers
├── api/            # FastAPI REST endpoints
├── plugins/        # Plugin system + builtin plugins
├── frameworks/     # AI framework abstractions (UnifiedLLM, etc.)
├── agents/         # Multi-agent coordination
├── iot/, mesh/, xr/ # Specialized feature modules
└── __main__.py    # CLI entry point

apps/gui/          # Electron desktop application
tests/             # Test suite organized by markers
docs/              # Documentation
```

## Key Files for Understanding the System

1. `CLAUDE.md` - Comprehensive development guide (read first!)
2. `ARCHITECTURE.md` - High-level system design
3. `README.md` - User-facing documentation
4. `windows_ai/core/orchestrator.py` - Heart of the system
5. `windows_ai/api/server.py` - API entry point
6. `build_exe.py` - Build configuration reference

## Extremely Detailed Development Guidelines

### Complete Manager Implementation Guide

Every manager in `windows_ai/integrations/` MUST follow this exact pattern:

```python
"""
{Domain} Manager for Windows AI
Handles all {domain}-related operations
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class {Domain}Manager:
    """
    Manages {domain} operations for Windows AI

    Features:
    - Feature 1
    - Feature 2
    - Feature 3

    Example:
        manager = {Domain}Manager(config)
        await manager.initialize()
        result = await manager.do_something()
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize manager with configuration

        Args:
            config: Configuration dictionary with:
                - api_key: API key for service (optional)
                - endpoint: Custom endpoint URL (optional)
                - timeout: Request timeout in seconds (default: 30)
                - retry_count: Number of retries (default: 3)
        """
        self.config = config
        self._initialized = False
        self._client = None
        self._cache = {}

        # Extract config values with defaults
        self.api_key = config.get("api_key", None)
        self.endpoint = config.get("endpoint", self._get_default_endpoint())
        self.timeout = config.get("timeout", 30)
        self.retry_count = config.get("retry_count", 3)

        logger.info(f"{self.__class__.__name__} created")

    def _get_default_endpoint(self) -> str:
        """Get default API endpoint"""
        return "https://api.example.com/v1"

    async def initialize(self) -> bool:
        """
        Initialize manager and establish connections

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            logger.warning(f"{self.__class__.__name__} already initialized")
            return True

        try:
            # Initialize client/connections
            if self.api_key:
                self._client = await self._create_client()
                logger.info(f"{self.__class__.__name__} client created")
            else:
                logger.warning(f"{self.__class__.__name__} initialized without API key")

            self._initialized = True
            logger.info(f"{self.__class__.__name__} initialized successfully")
            return True

        except Exception as e:
            logger.error(f"{self.__class__.__name__} initialization failed: {e}")
            return False

    async def _create_client(self):
        """Create and configure API client"""
        # Implement actual client creation
        pass

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        if self._client:
            await self._client.close()
        self._initialized = False
        logger.info(f"{self.__class__.__name__} cleaned up")

    # Implement actual functionality methods below
    async def do_something(self, param: str, **kwargs) -> Dict[str, Any]:
        """
        Main functionality method

        Args:
            param: Description of parameter
            **kwargs: Additional options

        Returns:
            Dictionary with:
                - success: Boolean indicating success
                - result: The actual result
                - error: Error message if failed

        Raises:
            ValueError: If param is invalid
            ConnectionError: If service unavailable
        """
        if not self._initialized:
            raise RuntimeError(f"{self.__class__.__name__} not initialized")

        try:
            # Implement actual functionality
            result = await self._do_something_internal(param, **kwargs)

            return {
                "success": True,
                "result": result,
                "error": None
            }

        except Exception as e:
            logger.error(f"{self.__class__.__name__}.do_something failed: {e}")
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }

    async def _do_something_internal(self, param: str, **kwargs):
        """Internal implementation"""
        # Actual implementation here
        pass
```

### Complete Plugin Implementation Guide

Every plugin MUST follow this structure:

```python
"""
{Plugin Name} Plugin
{Brief description of what this plugin does}
"""

from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class {PluginName}Plugin(Plugin):
    """
    {Detailed description of plugin functionality}

    Capabilities:
    - Capability 1
    - Capability 2
    - Capability 3

    Requirements:
    - Requirement 1 (e.g., API key)
    - Requirement 2 (e.g., external service)

    Example:
        plugin = {PluginName}Plugin()
        await plugin.initialize()
        result = await plugin.execute(param="value")
    """

    def __init__(self):
        """Initialize plugin with metadata"""
        metadata = PluginMetadata(
            id="{plugin-id}",
            name="{Plugin Name}",
            description="{Detailed description}",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,  # or ACTION, TOOL, UI, AUTOMATION
            tags=["tag1", "tag2", "tag3"],
            requirements=["package1", "package2"]
        )
        super().__init__(metadata)

        # Plugin-specific attributes
        self._client = None
        self._cache = {}

        logger.info(f"Plugin {self.metadata.id} created")

    async def initialize(self) -> bool:
        """
        Initialize plugin resources

        This is called once when the plugin is loaded.
        Setup connections, load resources, validate configuration.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Setup any required connections
            self._client = await self._setup_client()

            # Load any required resources
            await self._load_resources()

            # Validate configuration
            if not await self._validate_config():
                logger.error(f"Plugin {self.metadata.id} config validation failed")
                return False

            self._initialized = True
            logger.info(f"Plugin {self.metadata.id} initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Plugin {self.metadata.id} initialization failed: {e}")
            return False

    async def _setup_client(self):
        """Setup any required API clients"""
        # Implement client setup
        pass

    async def _load_resources(self):
        """Load any required resources"""
        # Implement resource loading
        pass

    async def _validate_config(self) -> bool:
        """Validate plugin configuration"""
        # Implement validation
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute plugin's main functionality

        This is the main entry point for plugin execution.
        Can be called multiple times after initialization.

        Args:
            **kwargs: Plugin-specific parameters

        Returns:
            Dictionary with:
                - status: "success" or "error"
                - result: The actual result data
                - error: Error message if status is "error"
                - metadata: Additional metadata about execution

        Example:
            result = await plugin.execute(
                param1="value1",
                param2="value2",
                options={"option1": True}
            )
        """
        if not self._initialized:
            return {
                "status": "error",
                "result": None,
                "error": "Plugin not initialized"
            }

        try:
            # Validate input parameters
            validated_params = await self._validate_params(**kwargs)

            # Execute main functionality
            result = await self._execute_internal(**validated_params)

            # Post-process result
            processed_result = await self._post_process(result)

            return {
                "status": "success",
                "result": processed_result,
                "error": None,
                "metadata": {
                    "plugin_id": self.metadata.id,
                    "plugin_version": self.metadata.version,
                    "execution_time": "..."  # Add timing info
                }
            }

        except ValueError as e:
            logger.error(f"Plugin {self.metadata.id} parameter validation failed: {e}")
            return {
                "status": "error",
                "result": None,
                "error": f"Invalid parameters: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Plugin {self.metadata.id} execution failed: {e}")
            return {
                "status": "error",
                "result": None,
                "error": str(e)
            }

    async def _validate_params(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize input parameters"""
        # Implement parameter validation
        return kwargs

    async def _execute_internal(self, **kwargs) -> Any:
        """Internal execution logic - implement plugin functionality here"""
        # THIS IS WHERE YOU IMPLEMENT THE ACTUAL PLUGIN LOGIC
        raise NotImplementedError("Plugin must implement _execute_internal()")

    async def _post_process(self, result: Any) -> Any:
        """Post-process execution result"""
        # Implement any result post-processing
        return result

    async def cleanup(self):
        """
        Cleanup plugin resources

        Called when the plugin is being unloaded.
        Close connections, save state, release resources.
        """
        try:
            if self._client:
                await self._client.close()

            self._initialized = False
            logger.info(f"Plugin {self.metadata.id} cleaned up")

        except Exception as e:
            logger.error(f"Plugin {self.metadata.id} cleanup failed: {e}")
```

### Complete API Route Development Guide

When adding new API endpoints, follow this pattern:

```python
# windows_ai/api/my_routes.py
"""
My Feature Routes
API endpoints for my feature
"""

from fastapi import APIRouter, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/my-feature",
    tags=["My Feature"],
    responses={404: {"description": "Not found"}}
)

# Request/Response models
class MyRequest(BaseModel):
    """Request model for my feature"""
    param1: str = Field(..., description="First parameter")
    param2: int = Field(0, description="Second parameter")
    options: Optional[Dict[str, Any]] = Field(None, description="Optional settings")

    class Config:
        schema_extra = {
            "example": {
                "param1": "example value",
                "param2": 42,
                "options": {"option1": True}
            }
        }

class MyResponse(BaseModel):
    """Response model for my feature"""
    status: str = Field(..., description="Operation status")
    result: Any = Field(..., description="Operation result")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

# Endpoints
@router.get("/", response_model=List[Dict[str, Any]])
async def list_items():
    """
    List all items

    Returns list of all items in the system.
    """
    try:
        # Implementation
        items = []  # Get items from manager
        return items
    except Exception as e:
        logger.error(f"Failed to list items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{item_id}", response_model=Dict[str, Any])
async def get_item(
    item_id: str = Path(..., description="Item ID")
):
    """
    Get specific item by ID

    Args:
        item_id: Unique identifier for the item

    Returns:
        Item details
    """
    try:
        # Implementation
        item = {}  # Get item from manager
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=MyResponse)
async def create_item(
    request: MyRequest = Body(..., description="Item data")
):
    """
    Create new item

    Args:
        request: Item creation parameters

    Returns:
        Created item details
    """
    try:
        # Validate request
        if not request.param1:
            raise HTTPException(status_code=400, detail="param1 is required")

        # Implementation
        result = {}  # Create item via manager

        return MyResponse(
            status="success",
            result=result,
            metadata={"created_at": "..."}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{item_id}", response_model=MyResponse)
async def update_item(
    item_id: str = Path(..., description="Item ID"),
    request: MyRequest = Body(..., description="Updated item data")
):
    """Update existing item"""
    try:
        # Implementation
        result = {}  # Update item via manager
        return MyResponse(status="success", result=result)
    except Exception as e:
        logger.error(f"Failed to update item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{item_id}")
async def delete_item(
    item_id: str = Path(..., description="Item ID")
):
    """Delete item"""
    try:
        # Implementation
        # Delete item via manager
        return {"status": "deleted", "item_id": item_id}
    except Exception as e:
        logger.error(f"Failed to delete item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Then register the router in `windows_ai/api/server.py`:**

```python
from windows_ai.api.my_routes import router as my_router

app.include_router(my_router, prefix="/api/v1")
```

### Complete Error Handling Strategy

**1. Manager-Level Error Handling**

```python
class MyManager:
    async def do_operation(self, param: str) -> Dict[str, Any]:
        """Operation with comprehensive error handling"""
        try:
            # Validate input
            if not param:
                return {
                    "success": False,
                    "error": "Parameter cannot be empty",
                    "error_type": "validation_error"
                }

            # Attempt operation
            result = await self._perform_operation(param)

            return {
                "success": True,
                "result": result,
                "error": None
            }

        except ConnectionError as e:
            # Specific error type
            logger.error(f"Connection failed: {e}")
            return {
                "success": False,
                "error": "Failed to connect to service",
                "error_type": "connection_error",
                "details": str(e)
            }

        except TimeoutError as e:
            logger.error(f"Operation timed out: {e}")
            return {
                "success": False,
                "error": "Operation timed out",
                "error_type": "timeout_error"
            }

        except ValueError as e:
            logger.error(f"Invalid value: {e}")
            return {
                "success": False,
                "error": "Invalid parameter value",
                "error_type": "validation_error",
                "details": str(e)
            }

        except Exception as e:
            # Catch-all for unexpected errors
            logger.exception(f"Unexpected error in do_operation: {e}")
            return {
                "success": False,
                "error": "An unexpected error occurred",
                "error_type": "internal_error",
                "details": str(e) if logger.level == logging.DEBUG else None
            }
```

**2. API-Level Error Handling**

```python
from fastapi import HTTPException, status

@router.post("/execute")
async def execute_operation(request: OperationRequest):
    """Execute operation with proper HTTP error codes"""
    try:
        # Validate request
        if not request.is_valid():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request parameters"
            )

        # Check authentication
        if not await is_authorized():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Check rate limits
        if await is_rate_limited():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        # Execute operation
        result = await manager.do_operation(request.param)

        if not result["success"]:
            # Convert manager error to HTTP error
            error_code = {
                "validation_error": status.HTTP_400_BAD_REQUEST,
                "connection_error": status.HTTP_503_SERVICE_UNAVAILABLE,
                "timeout_error": status.HTTP_504_GATEWAY_TIMEOUT,
                "internal_error": status.HTTP_500_INTERNAL_SERVER_ERROR
            }.get(result["error_type"], status.HTTP_500_INTERNAL_SERVER_ERROR)

            raise HTTPException(
                status_code=error_code,
                detail=result["error"]
            )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Unexpected errors
        logger.exception(f"Unexpected error in execute_operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
```

**3. Plugin-Level Error Handling**

```python
class MyPlugin(Plugin):
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute with graceful error handling"""
        try:
            # Pre-execution validation
            if not self._initialized:
                return self._error_response("Plugin not initialized")

            if not await self._validate_params(**kwargs):
                return self._error_response("Invalid parameters")

            # Execute with timeout
            async with asyncio.timeout(30):
                result = await self._execute_internal(**kwargs)

            return self._success_response(result)

        except asyncio.TimeoutError:
            return self._error_response("Operation timed out")

        except ValueError as e:
            return self._error_response(f"Validation error: {e}")

        except Exception as e:
            logger.exception(f"Plugin execution failed: {e}")
            return self._error_response(f"Execution failed: {e}")

    def _success_response(self, result: Any) -> Dict[str, Any]:
        """Create success response"""
        return {
            "status": "success",
            "result": result,
            "error": None
        }

    def _error_response(self, error: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "status": "error",
            "result": None,
            "error": error
        }
```

### Complete Logging Strategy

**1. Module-Level Logging Setup**

```python
import logging

# Create logger for this module
logger = logging.getLogger(__name__)

# In main application startup (windows_ai/__main__.py or api/server.py):
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('windows_ai.log'),
        logging.StreamHandler()
    ]
)
```

**2. Logging Best Practices**

```python
class MyManager:
    async def initialize(self):
        """Initialize with comprehensive logging"""
        logger.info(f"{self.__class__.__name__} initialization starting...")

        try:
            # Log important steps
            logger.debug("Loading configuration...")
            config = await self._load_config()

            logger.debug(f"Connecting to service at {self.endpoint}...")
            self._client = await self._create_client()

            logger.info(f"{self.__class__.__name__} initialized successfully")
            return True

        except ConnectionError as e:
            # Log errors with appropriate level
            logger.error(f"Failed to connect: {e}")
            return False

        except Exception as e:
            # Use exception() to include stack trace
            logger.exception(f"Initialization failed: {e}")
            return False

    async def process_data(self, data: Dict[str, Any]):
        """Process data with detailed logging"""
        logger.debug(f"Processing data: {data.keys()}")

        # Log warnings for unusual conditions
        if len(data) > 1000:
            logger.warning(f"Processing large dataset: {len(data)} items")

        # Log progress for long operations
        for i, item in enumerate(data):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(data)} items")

            await self._process_item(item)

        logger.info(f"Data processing complete: {len(data)} items processed")
```

**3. Logging Levels - When to Use Each**

```python
# DEBUG - Detailed information for diagnosing problems
logger.debug(f"Internal state: {self._internal_state}")
logger.debug(f"Calling API with params: {params}")

# INFO - Confirmation that things are working as expected
logger.info("Application started successfully")
logger.info(f"Processed {count} items in {duration}s")

# WARNING - Something unexpected but application can continue
logger.warning("API key not found, using default settings")
logger.warning(f"Slow operation: {operation} took {duration}s")

# ERROR - Error occurred but application can recover
logger.error(f"Failed to process item {item_id}: {error}")
logger.error("Database connection failed, retrying...")

# CRITICAL - Serious error, application may not be able to continue
logger.critical("Database unavailable - shutting down")
logger.critical(f"Out of memory: {memory_usage}")

# EXCEPTION - Error with full stack trace
try:
    risky_operation()
except Exception as e:
    logger.exception(f"Operation failed: {e}")
    # This automatically includes the full traceback
```

### Complete Configuration Management Guide

**1. Configuration File Structure**

```yaml
# config/default_config.yaml
application:
  name: "Windows AI"
  version: "2.0.0"
  environment: "production" # development, staging, production
  log_level: "INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL

api:
  host: "127.0.0.1"
  port: 8010
  cors_origins:
    - "http://localhost:3000"
    - "http://127.0.0.1:3000"
  rate_limit:
    enabled: true
    requests_per_minute: 60

orchestrator:
  auto_setup: true
  auto_install_dependencies: true
  max_concurrent_managers: 10
  manager_timeout_seconds: 30

managers:
  ai_providers:
    enabled: true
    default_provider: "openai"
    providers:
      openai:
        model: "gpt-4"
        temperature: 0.7
        max_tokens: 2000
      anthropic:
        model: "claude-3-opus"
        temperature: 0.7
        max_tokens: 4000

  image_generation:
    enabled: true
    default_provider: "dalle"
    providers:
      dalle:
        model: "dall-e-3"
        size: "1024x1024"
        quality: "standard"

plugins:
  auto_load: true
  plugin_directories:
    - "windows_ai/plugins/builtin"
    - "~/.windows_ai/plugins"
  disabled_plugins: []

performance:
  cache:
    enabled: true
    max_size_mb: 512
    ttl_seconds: 3600
  async_workers: 4
  max_memory_mb: 4096
```

**2. Loading Configuration**

```python
# windows_ai/config.py
import yaml
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager for Windows AI"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration

        Args:
            config_path: Path to config file (optional)
                        If not provided, uses default locations
        """
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()
        self._apply_env_overrides()

    def _find_config(self) -> str:
        """Find configuration file in standard locations"""
        locations = [
            # Current directory
            Path("config/default_config.yaml"),
            # User directory
            Path.home() / ".windows_ai" / "config.yaml",
            # Installation directory
            Path(__file__).parent.parent / "config" / "default_config.yaml"
        ]

        for location in locations:
            if location.exists():
                return str(location)

        # Return default location even if it doesn't exist
        return str(locations[0])

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()

    def _apply_env_overrides(self):
        """Override config with environment variables"""
        # API keys
        if api_key := os.getenv("OPENAI_API_KEY"):
            self.set("managers.ai_providers.providers.openai.api_key", api_key)

        if api_key := os.getenv("ANTHROPIC_API_KEY"):
            self.set("managers.ai_providers.providers.anthropic.api_key", api_key)

        # Application settings
        if log_level := os.getenv("LOG_LEVEL"):
            self.set("application.log_level", log_level)

        if env := os.getenv("ENVIRONMENT"):
            self.set("application.environment", env)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key

        Args:
            key: Configuration key (e.g., "api.port")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value by dot-notation key"""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "application": {
                "name": "Windows AI",
                "version": "2.0.0",
                "environment": "development",
                "log_level": "INFO"
            },
            "api": {
                "host": "127.0.0.1",
                "port": 8010
            },
            # ... more defaults
        }

# Global config instance
config = Config()
```

### Comprehensive Deployment Strategy

**1. Development Deployment**

```bash
# Start backend in development mode
python -m uvicorn windows_ai.api.server:app --reload --port 8010

# Start GUI in development mode
cd apps/gui
npm start

# Both will auto-reload on code changes
```

\*\*2. Production Build - Windows 3. `README.md` - User-facing documentation 4. `windows_ai/core/orchestrator.py` - Heart of the system 5. `windows_ai/api/server.py` - API entry point 6. `build_exe.py` - Build configuration reference

## Final Reminders

### 🚨 THE ABSOLUTE RULE 🚨

**DO NOT STOP UNTIL THE TASK IS 100% COMPLETE. THIS IS NON-NEGOTIABLE.**

When you start developing Windows AI:

1. Create comprehensive todo list with `manage_todo_list`
2. Mark tasks as "in-progress" one at a time
3. Complete ENTIRE task fully (not partially)
4. Mark as "completed" immediately after finishing
5. Start next task without delay
6. Continue until ALL tasks show "completed"
7. Only stop when verification confirms 100% completion

### ✅ Quality Checklist

Before declaring any component "complete":

- [ ] All code implemented (no stubs, no TODOs)
- [ ] All tests written and passing (60%+ coverage)
- [ ] All integration points working
- [ ] All error handling implemented
- [ ] All edge cases handled
- [ ] All documentation updated
- [ ] All security measures in place
- [ ] All performance optimizations applied
- [ ] Build system produces working artifacts
- [ ] Everything is production-ready

### 📊 Progress Tracking Template

```python
# Use this exact pattern for ALL development work
manage_todo_list(todoList=[
    {"id": 1, "title": "Task 1", "status": "not-started"},
    {"id": 2, "title": "Task 2", "status": "not-started"},
    # ... ALL tasks
])

# When starting
manage_todo_list(todoList=[
    {"id": 1, "title": "Task 1", "status": "in-progress"},
    {"id": 2, "title": "Task 2", "status": "not-started"},
])

# When completing
manage_todo_list(todoList=[
    {"id": 1, "title": "Task 1", "status": "completed"},
    {"id": 2, "title": "Task 2", "status": "in-progress"},
])

# Continue until ALL show "completed"
```

### 🎯 Success Criteria

Windows AI is ONLY complete when:

- ✅ All 43 managers fully implemented and tested
- ✅ All 200+ plugins functional
- ✅ API server runs without errors
- ✅ GUI launches and connects to backend
- ✅ All tests pass with 60%+ coverage
- ✅ Build system creates working executables
- ✅ Documentation is comprehensive and accurate
- ✅ Security measures all active
- ✅ Performance meets requirements
- ✅ Zero critical bugs

### 💡 Developer Mantras

Repeat these throughout development:

> "The task is not done until it's COMPLETELY done."

> "No placeholders. No stubs. No TODOs. Full implementation only."

> "Test coverage below 60% = task not complete."

> "If I'm thinking of stopping, I re-read CRITICAL RULE #1."

> "Every component is production-ready or it doesn't exist."

> "I continue executing until manage_todo_list shows 100% completion."

### 🔄 Continuous Execution Loop

```
┌─────────────────────────────────────┐
│ Start Development Task              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Create TODO List (manage_todo_list) │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Get Next Task (status=not-started)  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Mark as "in-progress"               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Implement FULLY (no partial work)   │
│ - Write code                        │
│ - Write tests                       │
│ - Update docs                       │
│ - Verify functionality              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Run Tests & Validate                │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Mark as "completed"                 │
└────────────┬────────────────────────┘
             │
             ▼
        ┌────────────┐
        │ More tasks?│
        └────┬───┬───┘
          YES│   │NO
             │   │
             │   ▼
             │ ┌─────────────────────────────┐
             │ │ Verify 100% Completion      │
             │ │ - All tests pass            │
             │ │ - All builds work           │
             │ │ - All features functional   │
             │ │ - Coverage 60%+             │
             │ └──────────────┬──────────────┘
             │                │
             │                ▼
             │           ┌─────────┐
             │           │ DONE ✅ │
             │           └─────────┘
             │
             └───────────────┘
             (Loop back to "Get Next Task")
```

### 🚫 NEVER Do These Things

1. ❌ Stop after reading files
2. ❌ Stop after planning
3. ❌ Stop after implementing one component
4. ❌ Ask "should I continue?" (answer is always YES)
5. ❌ Wait for user feedback mid-task
6. ❌ Leave TODO comments in code
7. ❌ Create stub implementations
8. ❌ Skip test writing
9. ❌ Declare victory before 100% complete

### ✅ ALWAYS Do These Things

1. ✅ Create comprehensive todo lists
2. ✅ Mark tasks in-progress before starting
3. ✅ Complete entire task before moving on
4. ✅ Mark completed immediately after finishing
5. ✅ Continue to next task without asking
6. ✅ Write full implementations (no placeholders)
7. ✅ Update documentation as you go
8. ✅ Verify functionality before marking complete
9. ✅ Only stop at 100% verified completion

### 📈 Efficiency Guidelines

**Work Fast AND Complete**:

- Use `multi_replace_string_in_file` for batch edits
- Read multiple files in parallel
- Build incrementally and verify frequently
- Don't over-analyze - implement, move forward

**Maintain Momentum**:

- No long pauses between tasks
- Don't re-read files unnecessarily
- Trust your implementation
- Keep todolist updated in real-time
- Work systematically through components

**Quality + Speed**:

- Fast doesn't mean sloppy
- Complete doesn't mean slow
- Find the sweet spot: thorough AND efficient
- Use templates and patterns (they're in this file!)
- Parallelize when possible

## Subagents - Specialized AI Assistants

You have access to 78 specialized subagents for ultra-fast development. Use `runSubagent` tool to invoke them.

### 🚀 Core Development Powerhouses

- **Architect** - System design, architecture decisions, technical planning, scalability strategies
- **CodeGenerator** - Rapid code generation from specifications, boilerplate automation
- **Refactor** - Code refactoring, modernization, optimization, tech debt elimination
- **Debugger** - Advanced debugging, root cause analysis, bug fixing, error tracing
- **PerformanceOptimizer** - Performance profiling, bottleneck elimination, optimization strategies

### 🎨 User Experience & Design

- **UXDesigner** - User experience design, usability testing, design systems, user research
- **LocalizationExpert** - i18n, multilingual support, cultural adaptation, locale management

### 💻 Specialized Technical Builders

- **APIDesigner** - REST/GraphQL API design and implementation, endpoint architecture
- **DatabaseExpert** - Schema design, query optimization, migrations, indexing strategies
- **FrontendBuilder** - React/Vue/Angular UI implementation, component architecture
- **BackendBuilder** - Server-side logic, business layer expert, API implementation
- **DevOpsEngineer** - CI/CD pipelines, infrastructure as code, deployment automation
- **MobileBuilder** - iOS/Android app development, cross-platform solutions
- **DesktopBuilder** - Electron/native desktop apps, Windows/Mac/Linux development

### 🤖 AI/ML Specialists

- **AIModelExpert** - Model selection, training, fine-tuning, deployment strategies
- **DataScientist** - Data analysis, ML pipelines, feature engineering, statistical modeling
- **NLPExpert** - Natural language processing, transformers, LLMs, text analysis
- **ComputerVisionExpert** - Image/video processing, object detection, CNN architectures
- **MLOpsEngineer** - ML deployment, monitoring, serving, model versioning

### 📚 Documentation & Communication

- **TechnicalWriter** - Comprehensive documentation creation, user guides, API docs
- **APIDocGenerator** - OpenAPI/Swagger documentation, API reference generation
- **DiagramCreator** - Architecture diagrams, flowcharts, UML, system visualizations
- **CommentGenerator** - Inline code documentation, docstring generation

### 📊 Data Engineering & Processing

- **DataEngineer** - ETL pipelines, data warehousing, streaming data, big data platforms
- **SearchOptimizer** - Elasticsearch, full-text search, search ranking, query optimization

### 🏗️ System Architecture & Patterns

- **EventDrivenArchitect** - Event sourcing, CQRS, message queues, event streaming
- **ScalabilityArchitect** - Horizontal scaling, sharding, load distribution, partitioning
- **ErrorRecoveryExpert** - Resilience patterns, retry logic, circuit breakers, fault tolerance

### ⚙️ Configuration & Infrastructure

- **ConfigurationManager** - Environment config, feature flags, secrets management
- **DependencyManager** - Package management, version resolution, dependency conflicts
- **VersionControlExpert** - Git workflows, branching strategies, merge conflict resolution

### 📡 Integration & Communication

- **SchemaDesigner** - API schema, database schema, data modeling, contract design
- **ProtocolExpert** - Network protocols, communication patterns, message formats
- **QueueSystemExpert** - Message queues, job queues, task distribution, worker management

### 🔍 Observability & Operations

- **APMExpert** - Application performance monitoring, profiling, instrumentation
- **MetricsEngineer** - Metrics collection, dashboards, KPIs, analytics
- **IncidentResponder** - Incident management, post-mortems, runbooks, on-call

### 🛠️ Developer Tools

- **CLIDesigner** - Command-line interfaces, argument parsing, interactive CLIs
- **ShellScriptingExpert** - Bash/PowerShell mastery, system automation, scripting
- **JSONSchemaExpert** - JSON Schema, validation, OpenAPI specs, contract testing

### 🚀 Advanced Capabilities

- **WorkflowEngineArchitect** - Workflow orchestration, state machines, DAGs
- **CrossPlatformExpert** - Multi-platform development, compatibility layers
- **NotificationSystemExpert** - Push notifications, email, SMS, webhooks, alerting

### 📊 Project Management Experts

- **ProjectPlanner** - Roadmaps, milestones, sprint planning, resource allocation
- **TaskBreaker** - Complex task decomposition, work breakdown structures
- **DependencyAnalyzer** - Dependency graphs, resolution, conflict management
- **RiskAssessor** - Risk identification, mitigation strategies, contingency planning

### ☁️ Infrastructure & Platform Specialists

- **CloudArchitect** - AWS/Azure/GCP multi-cloud expertise, cloud-native design
- **ContainerExpert** - Docker, Kubernetes, orchestration, containerization strategies
- **MicroservicesBuilder** - Distributed systems, service mesh, microservice architecture
- **ServerlessArchitect** - Lambda, Functions, event-driven architecture, FaaS
- **NetworkEngineer** - Load balancing, CDN, routing, network topology
- **DatabaseAdministrator** - DB tuning, replication, sharding, high availability

### 🎯 Domain-Specific Experts

- **BlockchainDeveloper** - Smart contracts, Web3, DeFi, blockchain architecture
- **GameDeveloper** - Unity, Unreal, game engines, game logic
- **EmbeddedSystemsExpert** - IoT, firmware, real-time systems, hardware integration
- **FinTechExpert** - Payment systems, compliance, financial security, transaction processing
- **HealthTechExpert** - HIPAA, medical systems, privacy compliance, healthcare workflows

### 🔬 Research & Analysis

- **ResearchAgent** - Technology research, trend analysis, competitive analysis
- **BenchmarkAnalyzer** - Performance benchmarking, comparisons, metrics analysis
- **TechStackAdvisor** - Technology selection, trade-offs, stack recommendations
- **PatternRecognizer** - Design patterns, best practices, anti-pattern detection

### ⚡ Automation & Optimization

- **WorkflowAutomator** - Automation pipelines, orchestration, workflow optimization
- **ScriptGenerator** - Bash/PowerShell/Python scripting, automation scripts
- **MigrationExpert** - Code/data migration, upgrades, version transitions
- **LegacyModernizer** - Legacy system modernization, code transformation
- **AlgorithmOptimizer** - Algorithm selection, complexity analysis, optimization
- **ConcurrencyExpert** - Async/await, threading, parallelization, race condition fixes

### 🎨 Windows AI Specialists

- **PluginArchitect** - Windows AI plugin design & implementation, plugin patterns
- **ManagerBuilder** - Integration manager creation, manager architecture
- **OrchestratorOptimizer** - Core orchestrator enhancement, coordination patterns
- **PromptEngineer** - Prompt engineering, LLM optimization, context management

### � Technical Excellence

- **CacheOptimizer** - Redis, Memcached, caching strategies, cache invalidation
- **MemoryOptimizer** - Memory profiling, leak detection, garbage collection tuning
- **CompilerExpert** - Build optimization, transpilation, compilation strategies
- **MonitoringExpert** - Observability, logging, metrics, tracing, alerting

### How to Use Subagents

```typescript
// Example: Use Architect for system design
runSubagent({
  agentName: "Architect",
  description: "Design microservices architecture",
  prompt:
    "Design a scalable microservices architecture for Windows AI with 10+ services, including API gateway, service discovery, and event bus.",
});

// Example: Use PerformanceOptimizer for bottleneck analysis
runSubagent({
  agentName: "PerformanceOptimizer",
  description: "Optimize performance",
  prompt:
    "Analyze Windows AI API server for performance bottlenecks, identify slow queries, optimize database access patterns, and implement caching strategies.",
});
```

<agents>
<!-- Core Development Powerhouses -->
<agent name="Architect"><description>Expert in system design, architecture decisions, technical planning, and scalability strategies</description></agent>
<agent name="CodeGenerator"><description>Rapid code generation from specifications, boilerplate automation, template-based development</description></agent>
<agent name="Refactor"><description>Code refactoring, modernization, optimization, technical debt elimination</description></agent>
<agent name="Debugger"><description>Advanced debugging, root cause analysis, bug fixing, error tracing</description></agent>
<agent name="PerformanceOptimizer"><description>Performance profiling, bottleneck elimination, optimization strategies</description></agent>

<!-- User Experience & Design -->

<agent name="UXDesigner"><description>User experience design, usability testing, design systems, user research</description></agent>
<agent name="LocalizationExpert"><description>i18n, multilingual support, cultural adaptation, locale management</description></agent>

<!-- Specialized Technical Builders -->

<agent name="APIDesigner"><description>REST/GraphQL API design and implementation, endpoint architecture</description></agent>
<agent name="DatabaseExpert"><description>Schema design, query optimization, migrations, indexing strategies</description></agent>
<agent name="FrontendBuilder"><description>React/Vue/Angular UI implementation, component architecture</description></agent>
<agent name="BackendBuilder"><description>Server-side logic, business layer expert, API implementation</description></agent>
<agent name="DevOpsEngineer"><description>CI/CD pipelines, infrastructure as code, deployment automation</description></agent>
<agent name="MobileBuilder"><description>iOS/Android app development, cross-platform solutions</description></agent>
<agent name="DesktopBuilder"><description>Electron/native desktop apps, Windows/Mac/Linux development</description></agent>

<!-- AI/ML Specialists -->

<agent name="AIModelExpert"><description>Model selection, training, fine-tuning, deployment strategies</description></agent>
<agent name="DataScientist"><description>Data analysis, ML pipelines, feature engineering, statistical modeling</description></agent>
<agent name="NLPExpert"><description>Natural language processing, transformers, LLMs, text analysis</description></agent>
<agent name="ComputerVisionExpert"><description>Image/video processing, object detection, CNN architectures</description></agent>
<agent name="MLOpsEngineer"><description>ML deployment, monitoring, serving, model versioning</description></agent>

<!-- Documentation & Communication -->

<agent name="TechnicalWriter"><description>Comprehensive documentation creation, user guides, API docs</description></agent>
<agent name="APIDocGenerator"><description>OpenAPI/Swagger documentation, API reference generation</description></agent>
<agent name="DiagramCreator"><description>Architecture diagrams, flowcharts, UML, system visualizations</description></agent>
<agent name="CommentGenerator"><description>Inline code documentation, docstring generation</description></agent>

<!-- Data Engineering & Processing -->

<agent name="DataEngineer"><description>ETL pipelines, data warehousing, streaming data, big data platforms</description></agent>
<agent name="SearchOptimizer"><description>Elasticsearch, full-text search, search ranking, query optimization</description></agent>

<!-- System Architecture & Patterns -->

<agent name="EventDrivenArchitect"><description>Event sourcing, CQRS, message queues, event streaming</description></agent>
<agent name="ScalabilityArchitect"><description>Horizontal scaling, sharding, load distribution, partitioning</description></agent>
<agent name="ErrorRecoveryExpert"><description>Resilience patterns, retry logic, circuit breakers, fault tolerance</description></agent>

<!-- Configuration & Infrastructure -->

<agent name="ConfigurationManager"><description>Environment config, feature flags, secrets management</description></agent>
<agent name="DependencyManager"><description>Package management, version resolution, dependency conflicts</description></agent>
<agent name="VersionControlExpert"><description>Git workflows, branching strategies, merge conflict resolution</description></agent>

<!-- Integration & Communication -->

<agent name="SchemaDesigner"><description>API schema, database schema, data modeling, contract design</description></agent>
<agent name="ProtocolExpert"><description>Network protocols, communication patterns, message formats</description></agent>
<agent name="QueueSystemExpert"><description>Message queues, job queues, task distribution, worker management</description></agent>

<!-- Observability & Operations -->

<agent name="APMExpert"><description>Application performance monitoring, profiling, instrumentation</description></agent>
<agent name="MetricsEngineer"><description>Metrics collection, dashboards, KPIs, analytics</description></agent>
<agent name="IncidentResponder"><description>Incident management, post-mortems, runbooks, on-call</description></agent>

<!-- Developer Tools -->

<agent name="CLIDesigner"><description>Command-line interfaces, argument parsing, interactive CLIs</description></agent>
<agent name="ShellScriptingExpert"><description>Bash/PowerShell mastery, system automation, scripting</description></agent>
<agent name="JSONSchemaExpert"><description>JSON Schema, validation, OpenAPI specs, contract testing</description></agent>

<!-- Advanced Capabilities -->

<agent name="WorkflowEngineArchitect"><description>Workflow orchestration, state machines, DAGs</description></agent>
<agent name="CrossPlatformExpert"><description>Multi-platform development, compatibility layers</description></agent>
<agent name="NotificationSystemExpert"><description>Push notifications, email, SMS, webhooks, alerting</description></agent>

<!-- Quality Assurance Masters -->

<agent name="QAEngineer"><description>Test planning, quality gates, automation strategies, test frameworks</description></agent>
<agent name="CodeReviewer"><description>Code review, best practices enforcement, style guide compliance</description></agent>
<agent name="IntegrationTester"><description>E2E testing, integration testing, system testing</description></agent>
<agent name="AccessibilityAuditor"><description>WCAG compliance, a11y testing, inclusive design</description></agent>

<!-- Project Management Experts -->

<agent name="ProjectPlanner"><description>Roadmaps, milestones, sprint planning, resource allocation</description></agent>
<agent name="TaskBreaker"><description>Complex task decomposition, work breakdown structures</description></agent>
<agent name="DependencyAnalyzer"><description>Dependency graphs, resolution, conflict management</description></agent>
<agent name="RiskAssessor"><description>Risk identification, mitigation strategies, contingency planning</description></agent>

<!-- Infrastructure & Platform Specialists -->

<agent name="CloudArchitect"><description>AWS/Azure/GCP multi-cloud expertise, cloud-native design</description></agent>
<agent name="ContainerExpert"><description>Docker, Kubernetes, orchestration, containerization strategies</description></agent>
<agent name="MicroservicesBuilder"><description>Distributed systems, service mesh, microservice architecture</description></agent>
<agent name="ServerlessArchitect"><description>Lambda, Functions, event-driven architecture, FaaS</description></agent>
<agent name="NetworkEngineer"><description>Load balancing, CDN, routing, network topology</description></agent>
<agent name="DatabaseAdministrator"><description>DB tuning, replication, sharding, high availability</description></agent>

<!-- Domain-Specific Experts -->

<agent name="BlockchainDeveloper"><description>Smart contracts, Web3, DeFi, blockchain architecture</description></agent>
<agent name="GameDeveloper"><description>Unity, Unreal, game engines, game logic</description></agent>
<agent name="EmbeddedSystemsExpert"><description>IoT, firmware, real-time systems, hardware integration</description></agent>
<agent name="FinTechExpert"><description>Payment systems, compliance, financial security, transaction processing</description></agent>
<agent name="HealthTechExpert"><description>HIPAA, medical systems, privacy compliance, healthcare workflows</description></agent>

<!-- Research & Analysis -->

<agent name="ResearchAgent"><description>Technology research, trend analysis, competitive analysis</description></agent>
<agent name="BenchmarkAnalyzer"><description>Performance benchmarking, comparisons, metrics analysis</description></agent>
<agent name="TechStackAdvisor"><description>Technology selection, trade-offs, stack recommendations</description></agent>
<agent name="PatternRecognizer"><description>Design patterns, best practices, anti-pattern detection</description></agent>

<!-- Automation & Optimization -->

<agent name="WorkflowAutomator"><description>Automation pipelines, orchestration, workflow optimization</description></agent>
<agent name="ScriptGenerator"><description>Bash/PowerShell/Python scripting, automation scripts</description></agent>
<agent name="MigrationExpert"><description>Code/data migration, upgrades, version transitions</description></agent>
<agent name="LegacyModernizer"><description>Legacy system modernization, code transformation</description></agent>
<agent name="AlgorithmOptimizer"><description>Algorithm selection, complexity analysis, optimization</description></agent>
<agent name="ConcurrencyExpert"><description>Async/await, threading, parallelization, race condition fixes</description></agent>

<!-- Windows AI Specialists -->

<agent name="PluginArchitect"><description>Windows AI plugin design & implementation, plugin patterns</description></agent>
<agent name="ManagerBuilder"><description>Integration manager creation, manager architecture</description></agent>
<agent name="OrchestratorOptimizer"><description>Core orchestrator enhancement, coordination patterns</description></agent>
<agent name="PromptEngineer"><description>Prompt engineering, LLM optimization, context management</description></agent>

<!-- Technical Excellence -->

<agent name="CacheOptimizer"><description>Redis, Memcached, caching strategies, cache invalidation</description></agent>
<agent name="MemoryOptimizer"><description>Memory profiling, leak detection, garbage collection tuning</description></agent>
<agent name="CompilerExpert"><description>Build optimization, transpilation, compilation strategies</description></agent>
<agent name="MonitoringExpert"><description>Observability, logging, metrics, tracing, alerting</description></agent>
</agents>
