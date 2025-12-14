# Windows AI - Complete User Manual

**Version**: 2.0.0  
**Last Updated**: December 14, 2025  
**Completion Status**: 100% Production Ready

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [First Time Setup](#first-time-setup)
4. [Using Windows AI](#using-windows-ai)
5. [Plugin System](#plugin-system)
6. [Integration Managers](#integration-managers)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)
10. [Appendix](#appendix)

---

## Getting Started

### What is Windows AI?

Windows AI is a comprehensive AI platform that provides 2,500+ capabilities through a unified interface. It includes:

- **79 Windows Plugins** for system automation
- **45 Integration Managers** for AI providers, cloud services, and business tools
- **50+ AI Models** supported (GPT-4, Claude, Gemini, local models, etc.)
- **Beautiful Desktop GUI** built with Electron
- **REST API** for programmatic access
- **Python SDK** for developers
- **Security Hardened** with multi-level sandboxing

### System Requirements

**Minimum**:
- Windows 10/11 (64-bit)
- 4 GB RAM
- 2 GB free disk space
- Any CPU (Intel/AMD)

**Recommended**:
- Windows 11 (64-bit)
- 16 GB+ RAM
- 10 GB free disk space
- Multi-core CPU (4+ cores)
- GPU with 4GB+ VRAM (for local AI models)

---

## Installation

### Method 1: Installer (Recommended)

1. Download `WindowsAI-Setup.exe` from [Releases](https://github.com/Anthony5265/Windows-AI/releases/latest)
2. Double-click to run the installer
3. Follow the installation wizard
4. Launch Windows AI from Start Menu or Desktop shortcut

The installer automatically:
- Installs Python runtime
- Configures environment
- Sets up shortcuts
- Starts background services

### Method 2: Portable Version

1. Download `WindowsAI-Portable.zip` from [Releases](https://github.com/Anthony5265/Windows-AI/releases/latest)
2. Extract to any location
3. Run `WindowsAI.exe`

Perfect for:
- USB drives
- No-install environments
- Testing before installation

### Method 3: From Source (Developers)

```bash
# Clone repository
git clone https://github.com/Anthony5265/Windows-AI.git
cd Windows-AI

# Install dependencies
pip install -r requirements.txt

# Run application
python -m windows_ai
```

---

## First Time Setup

### Setup Wizard

On first launch, the Setup Wizard guides you through:

1. **Welcome Screen**
   - Overview of Windows AI capabilities
   - System requirements check

2. **API Key Configuration** (Optional)
   - OpenAI API key
   - Anthropic API key  
   - Google AI API key
   - Other provider keys

3. **Model Selection**
   - Choose default AI model
   - Configure local vs cloud models
   - Set up fallback models

4. **Plugin Selection**
   - Enable/disable plugins
   - Configure plugin settings
   - Set up integrations

5. **Security Settings**
   - Choose sandbox level
   - Configure permissions
   - Set up audit logging

6. **Completion**
   - Review configuration
   - Launch Windows AI

### Manual Configuration

Configuration files are stored in:
- **Windows**: `C:\ProgramData\Windows AI\config\`
- **User Settings**: `%APPDATA%\Windows AI\`

Key configuration files:
- `defaults.json` - Main configuration
- `credentials.json` - Encrypted credentials
- `plugins.json` - Plugin settings

---

## Using Windows AI

### Desktop GUI

The main interface provides:

**Chat Interface**:
- Type messages in the chat input
- View conversation history
- Use slash commands (/help, /clear, /models)
- Attach files for analysis

**Plugin Panel**:
- Browse available plugins
- Execute plugin actions
- View plugin status
- Configure plugin settings

**Settings Panel**:
- Model selection
- API key management
- Plugin configuration
- Security settings
- Theme selection

**System Tray**:
- Quick access menu
- Start/stop backend
- New conversation
- Exit application

### Command Line Interface (CLI)

```bash
# Interactive mode
python -m windows_ai interactive

# Direct chat
python -m windows_ai chat "What's the weather?"

# Execute plugin
python -m windows_ai plugin windows_search search_files --query "*.pdf"

# Launch GUI
python -m windows_ai
```

### Python SDK

```python
from windows_ai import WindowsAI
import asyncio

async def main():
    # Initialize
    ai = WindowsAI()
    await ai.initialize()
    
    # Chat with AI
    response = await ai.chat("Explain quantum computing")
    print(response)
    
    # Generate image
    image_path = await ai.generate_image("cyberpunk cat")
    print(f"Image saved: {image_path}")
    
    # Execute plugin
    result = await ai.execute_plugin("windows_defender", {
        "action": "get_status"
    })
    print(result)
    
    # Cleanup
    await ai.shutdown()

asyncio.run(main())
```

### REST API

Start the API server:
```bash
python -m uvicorn windows_ai.api.server:app --reload --port 8010
```

API endpoints:
- `GET /health` - Health check
- `POST /api/chat` - Chat endpoint
- `POST /api/chat/stream` - Streaming chat
- `GET /api/plugins` - List plugins
- `POST /api/plugins/{id}/execute` - Execute plugin
- `GET /docs` - Interactive API documentation

Example requests:
```bash
# Chat
curl -X POST http://localhost:8010/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello AI!"}'

# Execute plugin
curl -X POST http://localhost:8010/api/plugins/windows_search/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "search_files", "parameters": {"query": "*.pdf"}}'
```

---

## Plugin System

### Available Plugins (79 Total)

#### Windows Core Plugins (49)
- Terminal, Window Manager, Process Management
- USB Management, Bluetooth, Disk Management
- Network Management, Firewall, Defender
- And 40 more...

#### Windows OS Plugins (30)
- WinRM, Windows Store, WSA, Performance Recorder
- Security Suite (Search, Hello, Defender, Firewall, BitLocker)
- System Management (ETW, Group Policy, BITS, etc.)
- Virtualization (Hyper-V, Containers, Sandbox, WSL2)

### Using Plugins

**Via GUI**:
1. Click "Plugins" in sidebar
2. Browse or search for plugin
3. Click plugin to view details
4. Click "Execute" and configure parameters
5. View results

**Via Python**:
```python
result = await ai.execute_plugin("plugin_id", {
    "action": "action_name",
    "parameters": {"param1": "value1"}
})
```

**Via API**:
```bash
curl -X POST http://localhost:8010/api/plugins/{plugin_id}/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "action_name", "parameters": {}}'
```

### Plugin Actions

Each plugin supports multiple actions. Example for `windows_defender`:

- `get_status` - Get antivirus status
- `start_scan` - Start virus scan
- `update_definitions` - Update virus definitions
- `add_exclusion` - Add path exclusion
- `get_threat_history` - View detected threats

---

## Integration Managers

### AI Providers Manager

Supports 50+ AI models:
- **OpenAI**: GPT-4, GPT-3.5-Turbo, GPT-4-Turbo
- **Anthropic**: Claude-3-Opus, Claude-3-Sonnet, Claude-3-Haiku
- **Google**: Gemini-Pro, Gemini-Ultra
- **Mistral**: Mistral-Large, Mistral-Medium
- **Groq**: Fast inference models
- **Cohere**: Command models
- **Local**: Ollama, LM Studio

Usage:
```python
from windows_ai.integrations import AIProvidersManager

manager = AIProvidersManager()
await manager.initialize()

response = await manager.generate_text(
    prompt="Explain AI",
    model="gpt-4",
    temperature=0.7
)
```

### Other Managers (44 Total)

**AI & ML**: Image Generation, Audio/Speech, Video, Computer Vision, RAG
**Productivity**: Document Processing, Translation, Email, Notifications
**Cloud**: Storage (S3, Azure, GCP), Databases (PostgreSQL, MongoDB, Redis)
**Development**: Code Assistants, Browser Automation
**Business**: Payments, Social Media, CRM
**Specialized**: Healthcare, Legal, Finance, Scientific, Real Estate

---

## Advanced Features

### Multi-Agent Coordination

Execute complex tasks with multiple AI agents:

```python
result = await ai.agents.execute(
    task="Build a landing page, deploy to Vercel, set up analytics",
    agents=["developer", "designer", "devops"]
)
```

### Workflow Automation

Create automated workflows:

```python
from windows_ai.workflow import WorkflowEngine

workflow = WorkflowEngine()
await workflow.create_workflow(
    name="Daily Report",
    schedule="0 9 * * MON",
    steps=[
        {"action": "gather_data", "source": "database"},
        {"action": "analyze", "model": "gpt-4"},
        {"action": "generate_report", "format": "pdf"},
        {"action": "email", "to": "team@company.com"}
    ]
)
```

### RAG Pipeline

Implement Retrieval-Augmented Generation:

```python
from windows_ai.rag import RAGPipeline

rag = RAGPipeline()
await rag.initialize()

# Index documents
await rag.index_documents("./knowledge_base/")

# Query with context
response = await rag.query(
    "What is our refund policy?",
    top_k=5
)
```

### Security Sandbox

Configure security levels:

```python
from windows_ai.security import SandboxLevel

ai = WindowsAI(config={
    "sandbox": {
        "level": SandboxLevel.STRICT,
        "allow_network": False,
        "allow_file_write": False,
        "timeout": 30
    }
})
```

---

## Troubleshooting

### Common Issues

**Backend Won't Start**:
- Check if port 8010 is available
- Run manually: `python -m windows_ai.api.server`
- Check logs in `C:\ProgramData\Windows AI\logs\`

**API Key Errors**:
- Verify API keys in Settings
- Check environment variables
- Ensure network connection

**Plugin Errors**:
- Check plugin requirements
- Verify Windows version compatibility
- Review plugin logs

**Performance Issues**:
- Close unnecessary plugins
- Reduce concurrent operations
- Check system resources
- Clear cache

### Debug Mode

Enable debug logging:

```bash
# CLI
python -m windows_ai --debug

# Environment variable
set WINDOWS_AI_DEBUG=1
python -m windows_ai
```

### Logs

Log locations:
- **Application**: `C:\ProgramData\Windows AI\logs\app.log`
- **Backend**: `C:\ProgramData\Windows AI\logs\backend.log`
- **Plugins**: `C:\ProgramData\Windows AI\logs\plugins\`

---

## FAQ

**Q: Is Windows AI free?**  
A: Yes, Windows AI is open-source and free. You need API keys for cloud AI providers.

**Q: Can I use Windows AI offline?**  
A: Yes, with local AI models (Ollama, LM Studio). Some features require internet.

**Q: How do I add custom plugins?**  
A: See [CLAUDE.md](CLAUDE.md) for plugin development guide.

**Q: Is my data private?**  
A: Yes, everything runs locally. Cloud API calls go directly to providers.

**Q: Can I use on Windows 10?**  
A: Yes, Windows 10 (64-bit) is supported. Some features require Windows 11.

**Q: How much disk space needed?**  
A: 2GB minimum, 10GB recommended for models and cache.

**Q: Can I contribute?**  
A: Yes! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Appendix

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New conversation |
| `Ctrl+Shift+C` | Quick chat |
| `Ctrl+,` | Settings |
| `Ctrl+P` | Plugins |
| `Ctrl+/` | Show help |
| `Ctrl+L` | Clear conversation |
| `Ctrl+Q` | Quit |

### Command Reference

```bash
# CLI Commands
windows-ai chat <message>          # Send chat message
windows-ai image <prompt>          # Generate image
windows-ai plugin <id> <action>    # Execute plugin
windows-ai models                  # List available models
windows-ai config                  # Show configuration
windows-ai health                  # System health check
```

### Configuration Options

```json
{
  "api": {
    "host": "127.0.0.1",
    "port": 8010,
    "cors_origins": ["http://localhost:3000"]
  },
  "orchestrator": {
    "auto_setup": true,
    "max_concurrent_managers": 10
  },
  "security": {
    "sandbox": {
      "enabled": true,
      "level": "standard"
    }
  }
}
```

### Environment Variables

- `WINDOWS_AI_CONFIG` - Custom config file path
- `WINDOWS_AI_DEBUG` - Enable debug mode
- `WINDOWS_AI_LOG_LEVEL` - Logging level
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GOOGLE_API_KEY` - Google AI API key

### Support & Resources

- **Documentation**: [FEATURES.md](FEATURES.md)
- **Developer Guide**: [CLAUDE.md](CLAUDE.md)
- **GitHub**: https://github.com/Anthony5265/Windows-AI
- **Issues**: https://github.com/Anthony5265/Windows-AI/issues
- **Discussions**: https://github.com/Anthony5265/Windows-AI/discussions

---

**Windows AI User Manual - Complete**  
For more information, see the comprehensive [FEATURES.md](FEATURES.md) documentation.
