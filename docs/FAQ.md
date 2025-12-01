# Windows AI - Frequently Asked Questions (FAQ)

Quick answers to common questions about Windows AI.

## General Questions

### What is Windows AI?

Windows AI is an intelligent assistant for Windows that uses local AI models to help you automate tasks, manage files, and interact with your system using natural language.

### Is Windows AI free?

Yes, Windows AI is open-source and completely free to use.

### Does it work offline?

Yes! Once you've downloaded an AI model, Windows AI works completely offline. No internet connection required for core functionality.

### Is my data private?

Yes. All AI processing happens locally on your computer. Your data never leaves your machine unless you explicitly use cloud-based plugins.

---

## Installation & Setup

### What are the system requirements?

**Minimum:**
- Windows 10 (64-bit) version 1809+
- 8 GB RAM
- 10 GB free disk space
- Intel Core i5 or equivalent

**Recommended:**
- Windows 11 (64-bit)
- 16 GB RAM
- 20 GB free disk space (for multiple models)
- Intel Core i7 or equivalent

### How much disk space do I need?

- **Application**: ~2 GB
- **Per AI model**: 4-40 GB depending on model size
- **Recommended total**: 10-20 GB

### Can I install on a different drive?

Yes, during installation choose "Custom" and select your preferred drive.

### Do I need administrator rights?

Yes, administrator rights are required for:
- Initial installation
- Installing Windows service
- First run only

After setup, the app runs with normal user privileges.

---

## Models & AI

### Which AI model should I use?

**For most users:**
- `llama2` (7B) - Best balance of speed and quality

**For developers:**
- `codellama` (7B) - Optimized for code

**For better quality (needs more RAM):**
- `llama2:13b` (13B) - Higher quality responses
- `mistral` (7B) - Alternative to llama2

### How do I download a model?

Three ways:

**1. From Chat:**
```
"Download the llama2 model"
```

**2. From Models Tab:**
- Go to Models tab
- Click "Browse Catalog"
- Find model
- Click "Download"

**3. From Command Line:**
```bash
cd "C:\Program Files\Windows AI"
ollama.exe pull llama2
```

### Can I use multiple models?

Yes! Download as many as you want and switch between them:
- Click model name in Chat tab
- Select different model
- Or set a default in Settings

### Why is model download slow?

Model downloads are large (4-40 GB). On a typical connection:
- **4 GB model**: 10-30 minutes
- **7 GB model**: 20-45 minutes
- **40 GB model**: 1-3 hours

Download runs in background - you can use the app while downloading.

### Can I use OpenAI/ChatGPT instead?

Yes, but requires API key (not recommended):
1. Get API key from OpenAI
2. Settings → Models → Add Cloud Model
3. Enter API key
4. Costs money per request

Local models (Ollama) are free and private.

---

## Features & Usage

### How do I automate folder organization?

1. Go to **Automation** tab
2. Click **[+ Add Watcher]**
3. Choose folder (e.g., Downloads)
4. Set rules (e.g., "Move PDFs to Documents")
5. Click **Save**

Now files are auto-organized!

### Can I schedule tasks?

Yes! Use the Automation tab:
1. Click **[+ Add Task]**
2. Set schedule (daily, weekly, custom)
3. Choose action
4. Save

Example: "Clean temp files every Monday at 3 AM"

### How do I install plugins?

**From Marketplace:**
1. Plugins tab → **[Browse Marketplace]**
2. Find plugin
3. Click **[Install]**
4. Enable it

**From file:**
1. Download `.zip` file
2. Plugins tab → ⚙️ → **Install from File**
3. Browse to file
4. Install

### What plugins are available?

500+ plugins including:
- File management
- System monitoring
- Development tools (Git, Docker)
- Productivity (Notion, Trello)
- Media tools (video, audio)
- And many more!

Browse at: Plugins tab → [Browse Marketplace]

---

## Troubleshooting

### App won't start

**Try these steps:**

1. **Restart Windows service:**
   ```
   Win+R → services.msc
   Find "WindowsAI" → Restart
   ```

2. **Check logs:**
   ```
   %APPDATA%\WindowsAI\logs\app.log
   ```

3. **Reinstall:**
   - Uninstall from Control Panel
   - Delete `C:\Program Files\Windows AI`
   - Reinstall

### Backend shows "Offline"

**Solutions:**

1. **Check service:**
   ```
   services.msc → WindowsAI → should be "Running"
   ```

2. **Test backend:**
   ```
   Browser: http://localhost:8010/health
   Should see: {"status": "healthy"}
   ```

3. **Check firewall:**
   Windows Defender → Allow "Windows AI" through firewall

### Model download fails

**Common causes:**

1. **Not enough disk space**
   - Need 5-10 GB free
   - Check: Settings → Models → Download Location

2. **Network issues**
   - Check internet connection
   - Try different model

3. **Firewall blocking**
   - Allow `ollama.exe` through firewall

### High RAM/CPU usage

**Solutions:**

1. **Use smaller model:**
   - Switch to `llama2:7b` instead of `13b` or `70b`

2. **Limit resources:**
   ```
   Settings → Advanced
   → Max RAM: 4 GB
   → CPU Threads: 4
   ```

3. **Disable watchers:**
   - Automation tab → Disable unused watchers

### Chat responses are slow

**Causes & solutions:**

1. **Large model on slow hardware**
   - Use smaller/faster model (llama2 vs mistral)

2. **Not enough RAM**
   - Close other apps
   - Use smaller model

3. **CPU bottleneck**
   - Upgrade hardware
   - Use GPU acceleration (if available)

### Uninstaller doesn't remove everything

After uninstalling, manually delete:

```
C:\Program Files\Windows AI  (if exists)
%APPDATA%\WindowsAI  (user data)
%LOCALAPPDATA%\WindowsAI  (cache)
```

---

## Privacy & Security

### Is my data collected?

No. By default:
- All AI runs locally
- No data sent to servers
- Chat history stored only on your PC

Optional telemetry (can be disabled):
- Anonymous usage statistics
- Crash reports

### Where is my data stored?

- **Chat history**: `%APPDATA%\WindowsAI\chats\`
- **Models**: `%APPDATA%\WindowsAI\models\` (or custom location)
- **Logs**: `%APPDATA%\WindowsAI\logs\`
- **Plugins**: `%APPDATA%\WindowsAI\plugins\`

### Can I delete my chat history?

Yes:
- **Single chat**: Chat tab → 🗑️ Clear History
- **All chats**: Settings → Privacy → Clear All Data
- **Manually**: Delete `%APPDATA%\WindowsAI\chats\`

### Is the app open source?

Yes! Source code available on GitHub:
https://github.com/yourorg/Windows-AI

### Are plugins safe?

- **Official plugins**: Vetted and safe
- **Community plugins**: Use caution, review code
- **Permissions**: Plugins request permissions before install

Always download plugins from trusted sources.

---

## Updates

### How do updates work?

Windows AI can auto-update:

**Automatic (default):**
1. App checks for updates daily
2. Downloads in background
3. Prompts you to install
4. Installs and restarts

**Manual:**
1. Settings → Updates → Check Now
2. Download update
3. Install when ready

### How do I disable auto-update?

Settings → Updates → Auto-check: Off

### Can I use beta versions?

Yes:
Settings → Updates → Channel → Beta

Warning: Beta versions may be unstable.

---

## Performance

### Why is Windows AI using so much RAM?

AI models are RAM-intensive:
- `llama2:7b`: ~4-6 GB RAM
- `llama2:13b`: ~8-10 GB RAM
- `llama2:70b`: ~40+ GB RAM

**To reduce RAM usage:**
- Use smaller model
- Settings → Advanced → Max RAM limit
- Close other apps

### Can I use GPU acceleration?

Yes, if you have compatible GPU:

**NVIDIA (CUDA):**
- Automatically detected
- No configuration needed

**AMD (ROCm):**
- Limited support
- May require manual setup

Check: Settings → Models → GPU Acceleration

### How can I make it faster?

1. **Use smaller/faster model**: `mistral` is faster than `llama2:13b`
2. **Enable GPU acceleration**: Settings → Models
3. **Close background apps**: Free up resources
4. **Use SSD**: Faster disk = faster model loading
5. **Increase RAM**: More RAM = better performance

---

## Advanced

### Can I use Windows AI from command line?

Yes! API available at `http://localhost:8010`

**Example (PowerShell):**
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8010/chat" `
    -Method POST `
    -Body '{"message": "Hello"}' `
    -ContentType "application/json"

$response.Content
```

See [API_REFERENCE.md](API_REFERENCE.md) for full API docs.

### Can I create custom plugins?

Yes! See [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md) for guide.

**Quick start:**
1. Create Python file in `windows_ai/plugins/custom/`
2. Implement plugin class
3. Register in `__init__.py`
4. Restart app

### Can I customize the AI's personality?

Yes, via system prompts:

Settings → Chat → System Prompt

**Example:**
```
You are a senior software engineer who explains
code clearly and concisely. Always provide working
examples.
```

### Can I run multiple instances?

No, only one instance can run at a time (backend uses port 8010).

**Workaround:**
- Run in VM
- Use different port (advanced configuration)

### Where can I get help?

- **Documentation**: [USER_GUIDE.md](USER_GUIDE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **GitHub Issues**: Report bugs
- **GitHub Discussions**: Ask questions
- **Discord**: Community chat

---

## Contributing

### How can I contribute?

- Report bugs on GitHub Issues
- Request features on GitHub Discussions
- Submit pull requests
- Create plugins
- Improve documentation

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### I found a bug!

Please report it:
1. Go to GitHub Issues
2. Check if already reported
3. If not, create new issue
4. Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Logs (`%APPDATA%\WindowsAI\logs\`)
   - Windows version
   - App version

---

## More Questions?

- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md) - Complete feature documentation
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed problem solving
- **API Docs**: [API_REFERENCE.md](API_REFERENCE.md) - For developers
- **GitHub**: https://github.com/yourorg/Windows-AI

Can't find your answer? Ask on GitHub Discussions!

---

*Last updated: 2025-01-10 | Windows AI v0.5.0*
