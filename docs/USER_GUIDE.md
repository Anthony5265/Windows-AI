# Windows AI - User Guide

Complete guide to all features and capabilities of Windows AI.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Interface Overview](#interface-overview)
4. [Chat Tab](#chat-tab)
5. [Automation Tab](#automation-tab)
6. [Plugins Tab](#plugins-tab)
7. [Models Tab](#models-tab)
8. [Settings](#settings)
9. [Advanced Features](#advanced-features)
10. [Keyboard Shortcuts](#keyboard-shortcuts)
11. [Troubleshooting](#troubleshooting)

---

## Introduction

Windows AI is an intelligent assistant that helps you automate tasks, manage files, and interact with your Windows system using natural language. It combines local AI models (Ollama) with powerful automation capabilities.

### Key Features

- 💬 **Natural Language Chat** - Talk to your computer naturally
- ⚙️ **File Automation** - Auto-organize folders, batch operations
- 🔌 **Extensible Plugins** - 500+ plugins for various tasks
- 🤖 **Local AI Models** - Privacy-first, runs entirely on your PC
- 📊 **System Monitoring** - Track CPU, RAM, disk usage
- 🔄 **Task Scheduling** - Cron-like automation
- 🎨 **Modern UI** - Clean, responsive Electron interface

---

## Installation

### System Requirements

**Minimum:**
- Windows 10 (64-bit) version 1809 or later
- Intel Core i5 or AMD Ryzen 5 processor
- 8 GB RAM
- 10 GB free disk space
- Internet connection (for initial setup)

**Recommended:**
- Windows 11 (64-bit)
- Intel Core i7 or AMD Ryzen 7 processor
- 16 GB RAM
- 20 GB free disk space (for multiple AI models)
- SSD for better performance

### Installation Steps

1. **Download Installer**
   ```
   Visit: https://github.com/yourorg/Windows-AI/releases
   Download: WindowsAI-Setup-v0.5.0.exe
   ```

2. **Run Installer**
   - Double-click the `.exe` file
   - Click "Yes" when Windows asks for administrator permission
   - This is required to install the Windows service

3. **Choose Installation Type**
   - **Typical** (Recommended): All components with defaults
   - **Custom**: Choose specific components
   - **Minimal**: Core only, no extras

4. **Select Components**

   | Component | Description | Required |
   |-----------|-------------|----------|
   | Core Components | Backend, GUI, runtime | ✅ Yes |
   | Windows Service | Auto-start on boot | ⭐ Recommended |
   | System Tray App | Quick access from taskbar | ⭐ Recommended |
   | Desktop Shortcuts | Icons on desktop | ☐ Optional |
   | First-Run Wizard | Setup assistant | ☐ Optional |
   | Documentation | Offline help files | ☐ Optional |

5. **Installation Progress**
   - Extracting files: ~1 minute
   - Installing Python dependencies: ~1-2 minutes
   - Installing Node.js dependencies: ~30 seconds
   - Configuring service: ~10 seconds
   - Total time: ~2-3 minutes

6. **Completion**
   - Check "Launch Windows AI" to start immediately
   - Click "Finish"

### Post-Installation

After installation, Windows AI will:
- ✅ Create `C:\Program Files\Windows AI\` directory
- ✅ Create `%APPDATA%\WindowsAI\` for user data
- ✅ Install Windows service "WindowsAI"
- ✅ Add Start Menu shortcuts
- ✅ Configure auto-start (if selected)

---

## Interface Overview

Windows AI has a modern, tabbed interface with 4 main sections:

```
┌─────────────────────────────────────────────────────┐
│  Windows AI                    ⚙️ Settings  ━ □ ✕   │
├─────────────────────────────────────────────────────┤
│  💬 Chat  │  ⚙️ Automation  │  🔌 Plugins  │  🤖 Models  │
├─────────────────────────────────────────────────────┤
│                                                     │
│                  Main Content Area                  │
│                                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Title Bar
- **App Name**: Windows AI
- **Settings**: ⚙️ icon opens preferences
- **Window Controls**: Minimize, Maximize, Close

### Tab Bar
Navigate between main features:
- **Chat** 💬: Conversation with AI
- **Automation** ⚙️: Folder watchers and tasks
- **Plugins** 🔌: Installed and available plugins
- **Models** 🤖: AI model management

### Status Bar (bottom)
- **Backend Status**: 🟢 Online / 🔴 Offline
- **Current Model**: Active AI model name
- **System Info**: CPU, RAM usage

---

## Chat Tab

The Chat tab is where you interact with AI using natural language.

### Interface Layout

```
┌─────────────────────────────────────────────────────┐
│  Model: llama2 (7B)                    🔄 ⚙️ 🗑️     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  User: Help me organize my Downloads folder         │
│                                                     │
│  AI: I can help you organize your Downloads folder. │
│      I found 47 files:                              │
│      - 12 PDFs                                      │
│      - 23 images (JPG, PNG)                        │
│      - 8 documents (DOCX, TXT)                     │
│      - 4 other files                               │
│                                                     │
│      Would you like me to:                         │
│      1. Move PDFs to Documents\PDFs                │
│      2. Move images to Pictures\Downloads          │
│      3. Move documents to Documents                │
│                                                     │
├─────────────────────────────────────────────────────┤
│  Type a message...                          [Send]  │
└─────────────────────────────────────────────────────┘
```

### Toolbar Icons
- 🔄 **New Chat**: Start fresh conversation
- ⚙️ **Chat Settings**: Temperature, max tokens
- 🗑️ **Clear History**: Delete current conversation

### Using Chat

**Basic Commands:**
```
"What files are in C:\Users\Me\Downloads?"
"Show me CPU usage"
"Find large files on C: drive"
"Help me clean up temp files"
```

**File Operations:**
```
"Move all PDFs from Downloads to Documents"
"Rename photos in C:\Vacation to include date"
"Delete files older than 30 days in C:\Temp"
"Find duplicate files in my Documents"
```

**System Information:**
```
"What's my disk space?"
"Show running processes"
"Check RAM usage"
"List installed programs"
```

**Automation:**
```
"Watch my Downloads folder and organize by type"
"Schedule disk cleanup every Monday at 3 AM"
"Alert me when C: drive is 90% full"
"Backup Documents folder every Friday"
```

### Advanced Chat Features

#### Context Awareness
AI remembers previous messages in the conversation:
```
You: "Find PDFs in Downloads"
AI: "Found 12 PDFs..."

You: "Move them to Documents"  ← AI knows "them" = PDFs
AI: "Moving 12 PDFs to Documents..."
```

#### File References
Refer to files by path:
```
"Summarize C:\Reports\quarterly_2024.pdf"
"Compare C:\data\old.csv and C:\data\new.csv"
"Extract text from C:\scans\document.png"
```

#### Multi-step Tasks
```
You: "I need to prepare my Downloads folder"
AI: "I can help. What would you like to do?"

You: "First, show me what's there"
AI: [Lists files]

You: "Delete anything older than 90 days"
AI: "Found 23 files. Delete them? [Yes/No]"

You: "Yes"
AI: "Deleted 23 files, freed 487 MB"
```

#### Code Execution
For code-related models (CodeLlama):
```
"Write a Python script to rename files"
"Explain this code: [paste code]"
"Debug this error: [paste error]"
```

### Chat Settings

Click ⚙️ to configure:

| Setting | Description | Default |
|---------|-------------|---------|
| Temperature | Creativity level (0-1) | 0.7 |
| Max Tokens | Response length limit | 2048 |
| System Prompt | AI personality/instructions | Default |
| Stream Responses | Show text as it's generated | Enabled |
| Save History | Remember conversations | Enabled |

---

## Automation Tab

Automate repetitive tasks with folder watchers and scheduled jobs.

### Folder Watchers

Monitor folders and automatically execute actions when files change.

**Interface:**
```
┌─────────────────────────────────────────────────────┐
│  Folder Watchers                      [+ Add Watcher]│
├─────────────────────────────────────────────────────┤
│                                                     │
│  📁 Downloads Organizer            ✅ Active       │
│     Folder: C:\Users\Me\Downloads                  │
│     Rule: Organize by file type                    │
│     Last run: 2 minutes ago                        │
│     [Edit] [Disable] [Delete]                      │
│                                                     │
│  📁 Screenshot Manager             ✅ Active       │
│     Folder: C:\Users\Me\Pictures\Screenshots       │
│     Rule: Rename with timestamp                    │
│     Last run: 10 minutes ago                       │
│     [Edit] [Disable] [Delete]                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Creating a Watcher:**

1. Click **[+ Add Watcher]**
2. **Configure Watcher:**
   - **Name**: "Downloads Organizer"
   - **Folder**: `C:\Users\Me\Downloads`
   - **Watch for**: New files, Modified files, Deleted files
   - **Action**: Organize by type, Move, Rename, Delete
3. **Set Rules:**
   - If file type is PDF → Move to `Documents\PDFs`
   - If file type is JPG/PNG → Move to `Pictures\Downloads`
   - If file type is ZIP → Move to `Archives`
4. Click **Save**

**Common Watcher Templates:**

**1. Downloads Organizer**
```yaml
Folder: C:\Users\{Username}\Downloads
Trigger: File created
Action: Move by extension
Rules:
  - .pdf, .doc, .docx → Documents
  - .jpg, .png, .gif → Pictures
  - .zip, .rar, .7z → Archives
  - .exe, .msi → Software
```

**2. Screenshot Manager**
```yaml
Folder: C:\Users\{Username}\Pictures\Screenshots
Trigger: File created
Action: Rename
Pattern: Screenshot_{YYYY-MM-DD}_{HHmmss}.png
```

**3. Temp File Cleaner**
```yaml
Folder: C:\Users\{Username}\AppData\Local\Temp
Trigger: Every hour
Action: Delete
Criteria: Files older than 7 days
```

**4. Backup Watcher**
```yaml
Folder: C:\Users\{Username}\Documents
Trigger: File modified
Action: Copy to backup
Destination: D:\Backups\Documents\{YYYY-MM-DD}
```

### Scheduled Tasks

Run tasks on a schedule, like cron.

**Interface:**
```
┌─────────────────────────────────────────────────────┐
│  Scheduled Tasks                      [+ Add Task]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🕐 Weekly Disk Cleanup          ✅ Enabled        │
│     Schedule: Every Monday at 3:00 AM              │
│     Task: Delete temp files, empty recycle bin     │
│     Next run: Monday, Jan 15 at 3:00 AM            │
│     [Edit] [Run Now] [Disable] [Delete]            │
│                                                     │
│  🕐 Daily Backup                 ✅ Enabled        │
│     Schedule: Every day at 6:00 PM                 │
│     Task: Backup Documents to D:\Backups           │
│     Next run: Today at 6:00 PM                     │
│     [Edit] [Run Now] [Disable] [Delete]            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Creating a Scheduled Task:**

1. Click **[+ Add Task]**
2. **Configure Task:**
   - **Name**: "Weekly Disk Cleanup"
   - **Description**: "Clean temporary files"
3. **Set Schedule:**
   - **Frequency**: Weekly
   - **Day**: Monday
   - **Time**: 3:00 AM
4. **Choose Action:**
   - **Run script**: Browse to script file
   - **Run command**: Type command
   - **Ask AI**: Use natural language
5. Click **Save**

**Schedule Formats:**

| Format | Example | Description |
|--------|---------|-------------|
| Daily | `Every day at 3:00 PM` | Runs once per day |
| Weekly | `Every Monday at 9:00 AM` | Specific day of week |
| Monthly | `1st of every month at 12:00 PM` | Specific day of month |
| Hourly | `Every hour` | Every hour on the hour |
| Custom Cron | `0 3 * * 1` | Advanced cron syntax |

**Common Task Examples:**

**Disk Cleanup:**
```
Schedule: Every Monday at 3:00 AM
Action: Delete temp files older than 30 days
Folders: C:\Windows\Temp, %TEMP%
```

**Document Backup:**
```
Schedule: Every day at 6:00 PM
Action: Copy Documents folder to D:\Backups
Include: Modified files only
Compression: ZIP
```

**System Report:**
```
Schedule: Every Sunday at 11:59 PM
Action: Generate system health report
Output: C:\Reports\weekly_{YYYY-MM-DD}.pdf
Include: Disk usage, RAM usage, CPU usage, Errors
```

---

## Plugins Tab

Extend Windows AI with plugins for specialized tasks.

### Interface

```
┌─────────────────────────────────────────────────────┐
│  Plugins                  [Browse Marketplace] [⚙️]  │
├─────────────────────────────────────────────────────┤
│  Installed (8)  │  Available (542)  │  Updates (2)  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ✅ File Manager                    v1.2.0         │
│     Advanced file operations and batch processing  │
│     [Configure] [Disable] [Uninstall]              │
│                                                     │
│  ✅ System Monitor                  v1.0.5         │
│     CPU, RAM, disk, network monitoring             │
│     [Configure] [Disable] [Uninstall]              │
│                                                     │
│  ✅ GitHub Integration              v2.1.0         │
│     Manage repos, issues, pull requests            │
│     [Configure] [Disable] [Uninstall]              │
│                                                     │
│  ☐ Docker Manager                  v1.5.2  [Update]│
│     Control Docker containers and images           │
│     [Enable] [Configure] [Uninstall]               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Built-in Plugins

These plugins come pre-installed:

**1. File Manager** (`file_manager_plugin`)
- Batch file operations
- Advanced search
- File metadata editing
- Duplicate finder

**2. System Monitor** (`system_monitor_plugin`)
- CPU usage tracking
- RAM monitoring
- Disk space analysis
- Network statistics

**3. Scheduler** (`scheduler_plugin`)
- Cron-like task scheduling
- One-time and recurring tasks
- Execution history

**4. Web Search** (`web_search_plugin`)
- Google, Bing, DuckDuckGo
- Search from chat interface
- Result summarization

**5. Screenshot** (`screenshot_plugin`)
- Capture screen regions
- Auto-save and organize
- OCR text extraction

### Installing Plugins

**From Marketplace:**

1. Click **[Browse Marketplace]**
2. Browse or search for plugins
3. Click plugin to view details
4. Click **[Install]**
5. Wait for installation
6. Click **[Enable]** to activate

**From File:**

1. Download plugin `.zip` file
2. Click ⚙️ → **Install from File**
3. Browse to `.zip` file
4. Click **Open**
5. Review permissions
6. Click **Install**

**From GitHub:**

1. Click ⚙️ → **Install from URL**
2. Paste repository URL
3. Click **Install**

### Configuring Plugins

Each plugin has its own settings:

1. Find plugin in list
2. Click **[Configure]**
3. Adjust settings
4. Click **Save**

**Example: GitHub Integration Config**
```yaml
Token: ghp_xxxxxxxxxxxxxxxxxxxx
Default Repo: username/repo-name
Auto-fetch: Every 10 minutes
Notifications: Enabled
```

### Popular Plugins

**Productivity:**
- **Notion Integration** - Sync with Notion workspace
- **Trello Bot** - Manage Trello boards
- **Slack Notifications** - Send Slack messages

**Development:**
- **VS Code Integration** - Open files in VS Code
- **Git Helper** - Git commands via chat
- **Docker Manager** - Container management

**Media:**
- **Video Converter** - Convert video formats
- **Audio Transcription** - Speech-to-text
- **Image Optimizer** - Compress images

**Utilities:**
- **Password Generator** - Secure passwords
- **QR Code Generator** - Create QR codes
- **Weather Forecast** - Local weather data

### Creating Custom Plugins

See [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md) for a complete guide.

---

## Models Tab

Manage AI models for different tasks.

### Interface

```
┌─────────────────────────────────────────────────────┐
│  AI Models                     [Browse Catalog] [⚙️]  │
├─────────────────────────────────────────────────────┤
│  Downloaded (2)  │  Available (47)  │  Custom (0)  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ⭐ llama2 (7B)                        4.1 GB      │
│     Fast general-purpose model                     │
│     [Set Default] [Delete]                         │
│                                                     │
│  codellama (7B)                       4.1 GB      │
│     Specialized for code tasks                     │
│     [Set Default] [Delete]                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Available Models

| Model | Size | Best For | RAM Needed |
|-------|------|----------|------------|
| **llama2** | 4 GB | General chat, tasks | 8 GB |
| **mistral** | 4 GB | Balanced performance | 8 GB |
| **codellama** | 4 GB | Code, programming | 8 GB |
| **llama2:13b** | 7 GB | Better quality | 16 GB |
| **mixtral** | 26 GB | High quality | 32 GB |
| **llama2:70b** | 39 GB | Best quality | 64 GB |

### Downloading Models

**Method 1: From Catalog**

1. Click **[Browse Catalog]**
2. Find model (e.g., "mistral")
3. Click **[Download]**
4. Wait for download (can take 10-30 minutes)
5. Model auto-appears in Downloaded tab

**Method 2: From Chat**

```
You: "Download the mistral model"
AI: "Downloading mistral (4.1 GB)..."
    [Progress: ████████░░ 80%]
AI: "Download complete! Set as default? [Yes/No]"
```

**Method 3: From CLI**

```bash
# In Windows AI installation directory
.\ollama.exe pull llama2
.\ollama.exe pull codellama
.\ollama.exe list  # Show downloaded models
```

### Switching Models

**During Chat:**
- Click model name in Chat tab header
- Select different model
- New model applies to next message

**Set Default:**
- Go to Models tab
- Find desired model
- Click **[Set Default]** ⭐

### Model Management

**Delete Model:**
1. Go to Models tab
2. Find model to remove
3. Click **[Delete]**
4. Confirm deletion
5. Disk space freed immediately

**Update Model:**
Models don't auto-update. To update:
1. Delete old version
2. Download new version from catalog

---

## Settings

Access settings via ⚙️ icon in title bar.

### General

- **Theme**: Dark / Light / Auto (system)
- **Language**: English (more coming soon)
- **Start on Boot**: Launch when Windows starts
- **Start Minimized**: Open to system tray
- **Auto-save Chats**: Save conversations
- **Chat History Limit**: 100 / 500 / 1000 / Unlimited

### Models

- **Default Model**: Choose primary AI model
- **Model Download Location**: Where to store models
- **Auto-download Updates**: Keep models current
- **GPU Acceleration**: Use NVIDIA/AMD GPU if available

### Privacy

- **Telemetry**: Send anonymous usage data
- **Crash Reports**: Send error reports
- **Model Training**: Don't use my data for training
- **Chat Storage**: Local only / Cloud sync

### Automation

- **Enable Folder Watchers**: Master on/off switch
- **Watcher Check Interval**: 1s / 5s / 10s / 30s
- **Max Concurrent Watchers**: Limit active watchers
- **Log Automation Events**: Save event log

### Updates

- **Auto-check for Updates**: Check daily/weekly/never
- **Auto-download Updates**: Download in background
- **Auto-install Updates**: Install without prompting
- **Update Channel**: Stable / Beta / Alpha

### Advanced

- **Backend Port**: Default 8010
- **Max RAM Usage**: Limit for AI models
- **CPU Threads**: Limit CPU cores used
- **Debug Mode**: Verbose logging
- **Developer Tools**: Enable Electron DevTools

---

## Advanced Features

### Command Palette

Press `Ctrl+Shift+P` to open command palette:

```
> Switch to Chat
> Download Model: llama2
> Enable Plugin: GitHub Integration
> Create Folder Watcher
> Export Chat History
> Check for Updates
```

Type to search and filter commands.

### Custom System Prompts

Define how AI behaves:

**Example: Helpful Assistant**
```
You are a helpful Windows automation assistant.
Be concise and practical. Always ask before
executing destructive operations like deleting files.
```

**Example: Code Expert**
```
You are a senior software engineer. Provide code
examples with best practices. Explain complex
concepts clearly. Use modern Python 3.11+ syntax.
```

### Scripting API

Automate Windows AI from Python/JavaScript:

**Python Example:**
```python
import requests

# Call Windows AI API
response = requests.post('http://localhost:8010/chat', json={
    'message': 'List files in Downloads',
    'model': 'llama2'
})

print(response.json()['reply'])
```

See [API_REFERENCE.md](API_REFERENCE.md) for full API docs.

---

## Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+Space` | Show/Hide Windows AI |
| `Ctrl+Shift+C` | Open Chat tab |
| `Ctrl+Shift+A` | Open Automation tab |
| `Ctrl+Shift+P` | Command Palette |

### Chat Tab

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New chat |
| `Ctrl+L` | Clear current chat |
| `Ctrl+K` | Focus chat input |
| `Ctrl+Enter` | Send message |
| `Ctrl+/` | Show chat shortcuts |
| `↑` / `↓` | Navigate chat history |

### General

| Shortcut | Action |
|----------|--------|
| `Ctrl+,` | Open Settings |
| `Ctrl+M` | Switch model |
| `Ctrl+Q` | Quit application |
| `Ctrl+R` | Reload window |
| `F11` | Toggle fullscreen |
| `F12` | Developer tools (if enabled) |

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Symptoms:**
- Double-clicking icon does nothing
- Taskbar icon appears then disappears
- Error message on startup

**Solutions:**

**Check logs:**
```
Location: %APPDATA%\WindowsAI\logs\app.log
Open: Win+R → type: %APPDATA%\WindowsAI\logs
```

**Restart Windows service:**
```
1. Win+R → services.msc
2. Find "WindowsAI"
3. Right-click → Restart
```

**Check port availability:**
```
netstat -ano | findstr :8010
```
If port 8010 is in use, change it in Settings.

**Reinstall:**
```
1. Uninstall from Control Panel
2. Delete C:\Program Files\Windows AI
3. Delete %APPDATA%\WindowsAI
4. Reinstall fresh
```

#### 2. Model Won't Download

**Symptoms:**
- Download starts but fails
- "Network error" message
- Download stuck at 0%

**Solutions:**

**Check disk space:**
```
Settings → Models → Model Download Location
Ensure 5-10 GB free space
```

**Check internet connection:**
```
ping ollama.ai
```

**Try different model:**
Some models may be temporarily unavailable.

**Manual download:**
```bash
cd "C:\Program Files\Windows AI"
ollama.exe pull llama2
```

#### 3. Backend Offline

**Symptoms:**
- Red "Offline" indicator
- Chat doesn't respond
- API errors

**Solutions:**

**Check service status:**
```
Win+R → services.msc
Find "WindowsAI" → Status should be "Running"
```

**Test backend:**
```
Open browser: http://localhost:8010/health
Should see: {"status": "healthy"}
```

**Check firewall:**
```
Windows Defender Firewall
→ Allow an app
→ Find "Windows AI"
→ Check "Private" and "Public"
```

**Restart backend:**
```
services.msc → WindowsAI → Restart
```

#### 4. High RAM/CPU Usage

**Symptoms:**
- Computer slow
- Fan running loud
- Task Manager shows high usage

**Solutions:**

**Limit resources:**
```
Settings → Advanced
→ Max RAM Usage: 4 GB
→ CPU Threads: 4
```

**Use smaller model:**
```
Switch from llama2:13b → llama2:7b
Smaller models use less RAM
```

**Close other apps:**
Free up system resources.

**Disable watchers temporarily:**
```
Automation tab → Disable all watchers
```

### Getting Help

**Check documentation:**
- [FAQ.md](FAQ.md) - Frequently asked questions
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting

**Community support:**
- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions
- Discord: Real-time help

**Logs location:**
```
Application: %APPDATA%\WindowsAI\logs\app.log
Backend: %APPDATA%\WindowsAI\logs\backend.log
Models: %APPDATA%\WindowsAI\logs\ollama.log
```

---

## Next Steps

- Read [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md) to create plugins
- See [API_REFERENCE.md](API_REFERENCE.md) for programmatic access
- Join community on Discord
- Contribute on GitHub

---

*Last updated: 2025-01-10 | Windows AI v0.5.0*
