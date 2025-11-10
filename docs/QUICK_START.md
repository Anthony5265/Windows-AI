# Windows AI - Quick Start Guide

Get up and running with Windows AI in just 5 minutes!

## Installation (2 minutes)

### System Requirements
- **OS**: Windows 10 (64-bit) or later
- **RAM**: 8 GB minimum, 16 GB recommended
- **Disk Space**: 10 GB free space
- **Internet**: Required for initial setup and model downloads

### Install Steps

1. **Download** the installer:
   - Go to [Releases](https://github.com/yourorg/Windows-AI/releases)
   - Download `WindowsAI-Setup-v0.5.0.exe`

2. **Run** the installer:
   - Double-click the downloaded `.exe` file
   - Click "Yes" when prompted for administrator privileges
   - Follow the installation wizard

3. **Choose components** (optional):
   - ✅ Core Components (required)
   - ✅ Windows Service (recommended - auto-start on boot)
   - ✅ System Tray Application (recommended)
   - ☐ Desktop Shortcuts (optional)
   - ☐ First-Run Wizard (helpful for beginners)

4. **Complete installation**:
   - Click "Install" and wait 2-3 minutes
   - App will launch automatically when done

## First Run (3 minutes)

### Initial Setup

When Windows AI launches for the first time:

1. **Welcome Screen** appears
   - Click "Get Started"

2. **Choose Your AI Model**:
   - **Ollama (Local)** - Runs on your PC, completely private
     - Recommended: `llama2` (4 GB) or `mistral` (4 GB)
     - Click "Download" next to your choice
   - **OpenAI (Cloud)** - More powerful, requires API key
     - Click "Configure API Key" and paste your key
   - You can add more models later!

3. **Quick Tour** (optional):
   - Learn the 4 main tabs: Chat, Automation, Plugins, Models
   - Skip if you prefer to explore on your own

### Your First Chat

1. Click the **Chat** tab (speech bubble icon)
2. Type a message: `"Help me organize my Downloads folder"`
3. Press **Enter** or click **Send**
4. Windows AI will:
   - Analyze your Downloads folder
   - Suggest organization strategies
   - Optionally execute them for you

**Example commands to try:**
```
"Summarize this PDF: C:\Documents\report.pdf"
"Find all images in my Pictures folder from last month"
"Schedule a task to clean temp files every Monday"
"What's using the most disk space on C:?"
```

## Main Features Overview

### 1. Chat Tab 💬
Talk to AI naturally. Ask questions, give commands, get help.

**Quick tips:**
- Use natural language: "Find large files" instead of complex commands
- Reference files by path: `C:\path\to\file.txt`
- Ask follow-up questions - AI remembers context
- Press `Ctrl+L` to clear chat history

### 2. Automation Tab ⚙️
Automate repetitive tasks and folder watching.

**Try this:**
1. Click "Add Watcher"
2. Select folder: `C:\Users\YourName\Downloads`
3. Set rule: "Move PDFs to Documents\PDFs"
4. Click "Save"
5. Now all PDFs in Downloads will auto-organize!

### 3. Plugins Tab 🔌
Extend functionality with plugins.

**Pre-installed plugins:**
- File Manager - Advanced file operations
- System Monitor - CPU, RAM, disk usage
- Scheduler - Cron-like task scheduling
- Web Search - Search directly from chat

**Install more:**
1. Click "Browse Marketplace"
2. Find a plugin (e.g., "GitHub Integration")
3. Click "Install"
4. Enable it in the list

### 4. Models Tab 🤖
Manage your AI models.

**Download a model:**
1. Click "Browse Catalog"
2. Choose a model:
   - `llama2` (4 GB) - Fast, good for most tasks
   - `codellama` (4 GB) - Great for code help
   - `mistral` (4 GB) - Balanced performance
3. Click "Download"
4. Set as default with the star icon

## Common Tasks

### Organize Files
```
Chat: "Organize my Downloads by file type"
```

### Clean Disk Space
```
Chat: "What's taking up space on my C: drive?"
Chat: "Delete temp files older than 30 days"
```

### Schedule Tasks
```
Chat: "Remind me to backup my Documents folder every Friday"
```

### File Search
```
Chat: "Find all PDFs modified in the last week"
```

### System Info
```
Chat: "Show me CPU and RAM usage"
Chat: "List all running processes using more than 500 MB RAM"
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New chat |
| `Ctrl+L` | Clear chat |
| `Ctrl+,` | Open settings |
| `Ctrl+M` | Switch model |
| `Ctrl+K` | Focus chat input |
| `Ctrl+Q` | Quit application |
| `F11` | Toggle fullscreen |

## Settings

Click the ⚙️ icon in the top-right to configure:

- **Theme**: Dark (default) or Light
- **Model**: Choose default AI model
- **Auto-start**: Launch Windows AI on boot
- **Notifications**: Enable/disable
- **Privacy**: Data collection preferences
- **Updates**: Auto-update settings

## Troubleshooting

### App won't start
1. Check logs: `%APPDATA%\WindowsAI\logs\app.log`
2. Try restarting the Windows service:
   - Open Services (`services.msc`)
   - Find "WindowsAI" service
   - Right-click → Restart

### Model won't download
1. Check disk space (need 5+ GB free)
2. Check internet connection
3. Try a different model
4. Check logs: `%APPDATA%\WindowsAI\logs\model.log`

### Backend offline
1. Check if service is running: `services.msc`
2. Try visiting `http://localhost:8010/health`
3. Restart the app
4. Check firewall isn't blocking port 8010

### More help
- Full guide: See [USER_GUIDE.md](USER_GUIDE.md)
- FAQ: See [FAQ.md](FAQ.md)
- Report bugs: [GitHub Issues](https://github.com/yourorg/Windows-AI/issues)

## What's Next?

### Learn More
- Read the [User Guide](USER_GUIDE.md) for detailed feature explanations
- Explore [Plugin Development](PLUGIN_DEVELOPMENT.md) to create custom plugins
- Check [API Reference](API_REFERENCE.md) for programmatic access

### Join the Community
- GitHub: https://github.com/yourorg/Windows-AI
- Discord: https://discord.gg/windows-ai
- Discussions: https://github.com/yourorg/Windows-AI/discussions

### Customize
- Create custom automation rules
- Install community plugins
- Train custom models (advanced)
- Integrate with your workflow

## Need Help?

- **Quick answers**: [FAQ.md](FAQ.md)
- **Issues**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Feature requests**: [GitHub Discussions](https://github.com/yourorg/Windows-AI/discussions)
- **Bugs**: [GitHub Issues](https://github.com/yourorg/Windows-AI/issues)

---

**Welcome to Windows AI!** 🎉

You're now ready to make your Windows experience smarter and more automated. Start chatting and see what's possible!

*Last updated: 2025-01-10*
