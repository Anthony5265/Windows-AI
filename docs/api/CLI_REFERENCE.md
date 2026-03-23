# Windows AI CLI Reference

## Overview

Windows AI provides a command-line interface for managing the platform, running diagnostics, and interacting with AI capabilities.

## Quick Start

```bash
# Launch GUI mode
python -m windows_ai

# Start interactive CLI
python -m windows_ai interactive

# Direct chat
python -m windows_ai chat "Hello, how are you?"

# Check system status
python -m windows_ai status

# Start API server
python -m windows_ai --api --port 8010
```

## Commands

### System Commands

| Command | Description |
|---------|-------------|
| `status` | Show system status, loaded managers, and plugin count |
| `health` | Run health checks on all components |
| `version` | Display Windows AI version |
| `capabilities` | List all available capabilities |

### Chat Commands

| Command | Description |
|---------|-------------|
| `chat "<message>"` | Send a chat message and get a response |
| `interactive` | Start an interactive chat session |

### Plugin Commands

| Command | Description |
|---------|-------------|
| `plugins list` | List all loaded plugins |
| `plugins search <query>` | Search plugins by keyword |
| `plugins enable <id>` | Enable a specific plugin |
| `plugins disable <id>` | Disable a specific plugin |

### Agent Commands

| Command | Description |
|---------|-------------|
| `agents list` | List active agents |
| `agents create <name>` | Create a new agent |

### Configuration Commands

| Command | Description |
|---------|-------------|
| `config get <key>` | Get a configuration value |
| `config set <key> <value>` | Set a configuration value |
| `config export` | Export current configuration |

### Mesh Commands

| Command | Description |
|---------|-------------|
| `mesh status` | Show mesh network status |
| `mesh peers` | List connected peers |

### Diagnostic Commands

| Command | Description |
|---------|-------------|
| `diagnostics benchmark` | Run performance benchmarks |
| `diagnostics connectivity` | Test network connectivity |

## API Server Mode

Start the FastAPI backend server:

```bash
# Default (port 8010)
python -m windows_ai --api

# Custom port
python -m windows_ai --api --port 9000

# With reload (development)
python -m uvicorn windows_ai.api.server:app --reload --port 8010
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WINDOWSAI_SERVER__PORT` | API server port | `8010` |
| `WINDOWSAI_LLM__PROVIDER` | Default LLM provider | `openai` |
| `WINDOWSAI_LLM__API_KEY` | LLM API key | — |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Configuration error |
| `3` | Dependency missing |
