# Getting Started with Windows AI

Welcome to Windows AI! This guide will help you set up and run the complete Windows AI system.

## 🎯 What's Been Built

Windows AI now has a **complete, functional chat interface** with:

✅ **FastAPI Backend** - Complete REST API with streaming support
✅ **Modern Chat GUI** - Beautiful Electron-based interface
✅ **Real-time Streaming** - AI responses stream in real-time
✅ **Conversation History** - All chats are saved and loadable
✅ **Multi-Model Support** - Support for OpenAI, Anthropic, Ollama
✅ **Dark/Light Themes** - Automatic theme detection
✅ **Settings Management** - Configurable AI parameters
✅ **Automation System** - Folder watchers and scheduled tasks
✅ **System Tray** - Quick command access with global hotkey

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (already installed ✅)
- **Node.js 22+** (already installed ✅)
- **Dependencies** (already installed ✅)

### Step 1: Start the Backend

The backend is the brain of Windows AI. It handles AI model communication and stores conversation history.

```bash
# Navigate to the project root
cd /home/user/Windows-AI

# Start the FastAPI backend
python3 -m uvicorn windows_ai.main:app --host 0.0.0.0 --port 8010 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8010 (Press CTRL+C to quit)
INFO:     Windows AI Backend starting up...
INFO:     Backend is ready!
```

**Backend is now running at:** `http://localhost:8010`

### Step 2: Start the Electron GUI

In a **new terminal window**:

```bash
# Navigate to the GUI directory
cd /home/user/Windows-AI/apps/gui

# Start the Electron application
npm start
```

The Windows AI chat interface should open automatically!

---

## 💬 Using Windows AI

### Chat Interface

1. **Type your message** in the input box at the bottom
2. **Press Enter** to send (Shift+Enter for new line)
3. **Watch the AI respond** in real-time with streaming
4. **Start a new chat** using the "New Chat" button
5. **Switch between conversations** using the sidebar

### Quick Actions

Click any quick action button to instantly send a prompt:
- **Organize Files** - Get help organizing your files
- **System Info** - View system information
- **Automation** - Automate repetitive tasks
- **Learn More** - Discover what Windows AI can do

### Model Selection

Choose your AI model from the dropdown:
- **GPT-3.5 Turbo** - Fast, cost-effective
- **GPT-4** - Most capable
- **GPT-4 Turbo** - Balanced performance
- **Claude 3 Sonnet** - Anthropic's model
- **Llama 2 (Local)** - Run locally via Ollama

### Settings

Click the **Settings** tab to configure:
- **Theme**: Light, Dark, or System
- **Backend Address**: Where the API is running
- **Default Model**: Your preferred AI model
- **Temperature**: Controls response creativity (0-1)

---

## 🔧 Configuration

### API Keys

To use cloud AI models, you need to set API keys:

```bash
# For OpenAI (GPT models)
export OPENAI_API_KEY="your-api-key-here"

# For Anthropic (Claude models)
export ANTHROPIC_API_KEY="your-api-key-here"

# Then restart the backend
```

### Local Models (Ollama)

To use local AI models without API keys:

1. **Install Ollama**: https://ollama.ai
2. **Download a model**: `ollama pull llama2`
3. **Ollama runs on**: `http://localhost:11434`
4. **Select** "Llama 2 (Local)" in the model dropdown

Windows AI will automatically use Ollama through LiteLLM!

---

## 📂 Project Structure

```
Windows-AI/
├── windows_ai/
│   ├── main.py                 # 🔥 Main FastAPI backend (NEW!)
│   ├── agents.py               # Agent protocol
│   ├── system_info.py          # System integration
│   └── ...
├── apps/
│   └── gui/
│       ├── main.js             # Electron main process
│       ├── preload.js          # IPC bridge
│       └── renderer/
│           ├── index.html      # 🔥 Modern chat UI (NEW!)
│           ├── styles.css      # 🔥 Beautiful styling (NEW!)
│           └── renderer.js     # 🔥 Chat functionality (NEW!)
├── apps/actions-api/           # Express API (TypeScript)
├── windows-ai-agent/           # Node.js agent service
├── windows-ai-tray/            # System tray app
└── ...
```

---

## 🎨 Features Showcase

### Chat Interface
- **Modern Design**: Clean, professional interface
- **Responsive**: Works on any screen size
- **Smooth Animations**: Typing indicators, message fade-ins
- **Message Bubbles**: Clear distinction between user and AI
- **Timestamps**: Every message is timestamped
- **Avatar Icons**: Visual identity for user and AI

### Streaming Responses
- **Real-time**: See AI responses as they're generated
- **No Waiting**: Start reading while AI is still thinking
- **Smooth**: Character-by-character streaming

### Conversation Management
- **Auto-save**: Every conversation is saved automatically
- **History**: Access all your past conversations
- **Resume**: Pick up where you left off
- **Preview**: See first message in sidebar

### Themes
- **Light Mode**: Bright, clean interface
- **Dark Mode**: Easy on the eyes
- **System**: Follows your OS preference
- **Instant Switch**: Change themes on the fly

### 🤖 Automation

Windows AI includes powerful automation features to make your workflows intelligent and proactive.

#### Folder Watchers

Monitor directories for file changes and trigger AI actions automatically:

1. **Navigate to Automation Tab**: Click the "Automation" tab in the GUI
2. **Add a Watcher**: Click "+ Add Watcher"
3. **Configure**:
   - **Name**: e.g., "Downloads Organizer"
   - **Folder Path**: Path to monitor (e.g., `/home/user/Downloads`)
   - **File Patterns**: Comma-separated patterns (e.g., `*.pdf, *.docx`)
   - **Events**: Select which events to watch (created, modified, deleted)
   - **Action**: Choose what AI should do:
     - **Organize** - Sort files into folders
     - **Summarize** - Create document summaries
     - **Analyze** - Analyze file content
     - **Custom** - Write your own prompt
4. **Save**: The watcher starts automatically

**Example Use Cases:**
- Auto-organize downloads into categorized folders
- Summarize PDFs when they arrive
- Analyze log files for errors
- Backup important documents

#### Scheduled Tasks

Run AI tasks on a schedule:

1. **Navigate to Automation Tab**: Click the "Automation" tab
2. **Add a Task**: Click "+ Add Task"
3. **Configure**:
   - **Name**: e.g., "Daily Summary"
   - **Description**: What the task does
   - **Schedule Type**:
     - **Interval**: Run every N hours/minutes (e.g., `1h`, `30m`, `2d`)
     - **Cron**: Use cron expressions (e.g., `0 9 * * *` for 9 AM daily)
     - **Once**: Run at a specific time
   - **Schedule**: The schedule value
   - **Action**: Type of task to run
   - **Prompt**: Instructions for the AI
4. **Save**: Task will run according to schedule

**Example Use Cases:**
- Daily morning briefing at 9 AM
- Hourly system health checks
- Weekly cleanup and organization
- End-of-day summaries

#### Managing Automations

- **Toggle On/Off**: Click the play/pause button
- **Delete**: Click the trash icon
- **View Status**: See if watchers are running and when tasks last ran
- **Next Run Time**: Scheduled tasks show when they'll execute next

---

## 🧪 Testing the System

### Test 1: Backend Health Check
```bash
curl http://localhost:8010/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "backend": "running",
    ...
  }
}
```

### Test 2: Send a Chat Message
```bash
curl -X POST http://localhost:8010/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, who are you?",
    "model": "gpt-3.5-turbo"
  }'
```

### Test 3: List Conversations
```bash
curl http://localhost:8010/conversations
```

---

## 📊 What Data is Stored?

Windows AI stores data locally in your home directory:

```
~/.windows-ai/
├── chat_history.json    # All your conversations
└── config.json          # Your settings
```

**Your data stays on your computer** - nothing is sent to third parties except AI API calls.

---

## 🔍 Troubleshooting

### Backend won't start
- **Check port**: Make sure port 8010 is not in use
- **Check Python**: Ensure Python 3.11+ is installed
- **Check dependencies**: Run `pip install -r requirements.txt`

### GUI won't connect to backend
- **Check status bar**: Look at the bottom of the window
- **Check backend**: Make sure it's running at http://localhost:8010
- **Check console**: Open DevTools (Ctrl+Shift+I) for errors

### AI not responding
- **Check API keys**: Set OPENAI_API_KEY or use local models
- **Check model**: Try switching to a different model
- **Check backend logs**: Look for errors in the terminal

### "Backend offline" message
- **Start backend first**: Backend must be running before GUI
- **Check URL**: Settings → Network → Backend Address
- **Check firewall**: Allow localhost connections

---

## 🚀 Next Steps

### For Users
1. **Set up API keys** for cloud models
2. **Or install Ollama** for local AI
3. **Start chatting** with your AI assistant!
4. **Explore automation** in the Workflows tab

### For Developers
1. **Explore the codebase** - well-documented and organized
2. **Add plugins** - see `windows-ai-agent/src/plugins/`
3. **Create workflows** - see `automation/` directory
4. **Customize themes** - modify `renderer/styles.css`
5. **Extend AI capabilities** - add new endpoints to `windows_ai/main.py`

---

## 🎯 What's Working

✅ **Complete Chat System**
- Send messages
- Receive AI responses
- Streaming responses
- Conversation history
- Multi-model support

✅ **Beautiful UI**
- Modern design
- Light/dark themes
- Responsive layout
- Smooth animations

✅ **Backend API**
- RESTful endpoints
- WebSocket support
- Conversation management
- Configuration system

✅ **Settings**
- Theme switching
- Model selection
- Parameter tuning
- Network configuration

---

## 🔮 Roadmap

### Short Term
- [ ] System tray quick commands
- [ ] Windows service integration
- [ ] Keyboard shortcuts (global hotkeys)
- [ ] File drag-and-drop support
- [ ] Voice input

### Medium Term
- [ ] Task automation workflows
- [ ] File system integration
- [ ] Calendar/reminder integration
- [ ] Screen capture and analysis
- [ ] Context menu integration

### Long Term
- [ ] Mesh home network integration
- [ ] IoT device control
- [ ] Mobile companion app
- [ ] Windows installer (.exe)
- [ ] Auto-updates

---

## 🤝 Contributing

Windows AI is actively being developed! Contributions are welcome:

1. **Report bugs** - Open an issue
2. **Suggest features** - Share your ideas
3. **Submit PRs** - Help build the future
4. **Documentation** - Improve these guides

---

## 📄 License

See LICENSE file for details.

---

## 🎉 Congratulations!

You now have a fully functional AI assistant running on your Windows PC!

**Enjoy your conversations with Windows AI!** 🚀

---

## 📞 Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Check the `/docs` directory

---

*Built with ❤️ for the future of personal computing*
