# Windows AI - Release Package

Welcome to Windows AI v0.2.0! This package contains everything you need to run Windows AI on your Windows computer.

## 📦 What's Included

This release package contains:

- **WindowsAI Installer** - Complete Windows installer with NSIS (both x64 and x86)
- **Portable Version** - No-installation executable
- **Backend Server** - Python FastAPI backend for AI processing
- **Documentation** - Complete user and developer documentation
- **Configuration Files** - Default settings and sample configs

## 🚀 Quick Start

### For End Users (Recommended)

1. **Run the Installer**
   - Double-click `WindowsAI-0.2.0-x64.exe` (or `ia32` for 32-bit)
   - Follow the installation wizard
   - Launch from Start Menu → "Windows AI"

2. **Configure Your AI Provider**
   - Open Settings (⚙️ icon in GUI)
   - Go to "API Keys"
   - Add your OpenAI API key or Anthropic API key
   - Or configure local Ollama server

3. **Start Using Windows AI**
   - Type your questions in the chat
   - Press `Ctrl+Shift+Space` anywhere for quick access
   - Explore automation features in Settings

### For Developers & Advanced Users

1. **Install Python Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the Backend**
   ```bash
   # On Windows
   start-backend.bat

   # On Linux/Mac
   ./start-backend.sh
   ```

3. **Run the GUI**
   - Launch the installed Windows AI app, or
   - Run from source: `npm start` in the GUI directory

## 🔑 API Key Setup

Windows AI supports multiple AI providers:

### OpenAI (GPT-3.5, GPT-4)
1. Get API key from https://platform.openai.com/api-keys
2. Add to Windows AI Settings → API Keys → OpenAI

### Anthropic (Claude)
1. Get API key from https://console.anthropic.com/
2. Add to Windows AI Settings → API Keys → Anthropic

### Local Ollama (Free, No API Key)
1. Install Ollama from https://ollama.ai/
2. Run: `ollama serve`
3. Windows AI will automatically detect local Ollama

## 📚 Documentation

- **README.md** - Project overview and features
- **GETTING_STARTED.md** - Detailed setup and usage guide
- **RELEASE_NOTES.md** - What's new in this version
- **CHANGELOG.md** - Complete version history
- **CONTRIBUTING.md** - How to contribute to the project

## 🎯 Key Features

### Chat Interface
- Real-time AI conversations with streaming responses
- Support for GPT-3.5, GPT-4, Claude, and local models
- Persistent conversation history
- Beautiful dark/light themes

### Automation
- **Folder Watchers**: Monitor folders and trigger AI actions
- **Task Scheduler**: Run AI tasks on a schedule
- **Custom Actions**: Create your own automation workflows

### Plugins
- Web Search (DuckDuckGo)
- File Organizer
- System Information
- GitHub Integration
- Code Executor
- Calendar & Reminders

### System Integration
- System tray with global hotkey (`Ctrl+Shift+Space`)
- Desktop notifications
- Quick command access
- Minimal resource usage

## 🖥️ System Requirements

- **Operating System**: Windows 10 or later
- **Processor**: x64 or x86 (32-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for application
- **Internet**: Required for cloud AI providers (OpenAI, Anthropic)

## 🛠️ Troubleshooting

### GUI Won't Start
- Check if port 8010 is available (backend port)
- Check backend logs in `backend.log`
- Try running `start-backend.bat` manually

### Can't Connect to AI
- Verify API key is correctly entered
- Check internet connection
- Ensure you have API credits (OpenAI/Anthropic)
- For Ollama: Verify `ollama serve` is running

### Backend Issues
- Ensure Python 3.11+ is installed
- Run: `pip install -r requirements.txt` in backend folder
- Check `backend.log` for error messages

### Installation Issues
- Run installer as Administrator
- Disable antivirus temporarily during installation
- Check Windows Event Viewer for error details

## 🔒 Privacy & Security

- **Local Processing**: All data stays on your machine except AI API calls
- **API Keys**: Stored encrypted on your local machine
- **No Telemetry**: Windows AI doesn't collect usage data
- **Open Source**: Full source code available for audit

## 📝 Configuration Files

### Backend Configuration
- Location: `backend/config/`
- Default settings in `defaults.json`
- User settings in `%PROGRAMDATA%/Windows AI/config/`

### Conversation History
- Stored in: `%APPDATA%/Windows AI/conversations/`
- JSON format, one file per conversation
- Can be backed up or deleted safely

## 🚀 Advanced Usage

### Command Line Options

**Backend:**
```bash
python -m windows_ai.main --host 0.0.0.0 --port 8010
```

**Custom Model:**
```bash
# Set environment variable
set LITELLM_MODEL=gpt-4
start-backend.bat
```

### REST API
Backend exposes REST API on `http://localhost:8010`

Key endpoints:
- `POST /chat` - Send chat messages
- `GET /chat/stream` - Stream responses
- `GET /conversations` - List conversations
- `POST /automation/watchers` - Create folder watcher
- `GET /plugins` - List plugins

API documentation: `http://localhost:8010/docs`

## 🤝 Getting Help

- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Documentation**: See `/docs` folder for detailed guides
- **Source Code**: https://github.com/Anthony5265/Windows-AI

## 📄 License

Windows AI is released under the MIT License. See LICENSE file for details.

## 🙏 Credits

Built with:
- Electron - Desktop app framework
- FastAPI - Backend REST framework
- LiteLLM - Multi-model AI integration
- Python & Node.js - Core languages

## 📞 Support & Feedback

We'd love to hear from you!
- Star the project on GitHub ⭐
- Report bugs and request features via GitHub Issues
- Contribute code via Pull Requests
- Share your automation workflows with the community

---

**Enjoy using Windows AI!** 🎉

For the latest updates, visit: https://github.com/Anthony5265/Windows-AI
