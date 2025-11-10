# Windows AI - Troubleshooting Guide

Detailed solutions for common problems and issues with Windows AI.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Startup Problems](#startup-problems)
3. [Backend/Service Issues](#backendservice-issues)
4. [Model Download Problems](#model-download-problems)
5. [Chat/AI Issues](#chatai-issues)
6. [Automation Problems](#automation-problems)
7. [Plugin Issues](#plugin-issues)
8. [Performance Problems](#performance-problems)
9. [Network/Connectivity Issues](#networkconnectivity-issues)
10. [Uninstallation Issues](#uninstallation-issues)
11. [Log Files](#log-files)
12. [Getting Help](#getting-help)

---

## Installation Issues

### Installer Won't Run

**Symptoms:**
- Double-clicking `.exe` does nothing
- "This app can't run on your PC" error
- Installer crashes immediately

**Solutions:**

**1. Check System Requirements**
```
Minimum: Windows 10 (64-bit) version 1809+
Check your version:
Win+R → winver
```

**2. Run as Administrator**
- Right-click installer
- Select "Run as administrator"
- Click "Yes" when prompted

**3. Disable Antivirus Temporarily**
- Some antivirus software blocks unsigned installers
- Add Windows AI to exclusions
- Or temporarily disable antivirus during install

**4. Check Disk Space**
```
Need: 10 GB free minimum
Check: Right-click C: → Properties
```

**5. Re-download Installer**
- Download may be corrupted
- Download from official source only
- Verify checksum (if provided)

### "Access Denied" During Installation

**Cause:** Insufficient privileges or locked files

**Solutions:**

**1. Close Running Instances**
```powershell
# Check if Windows AI is running
Get-Process | Where-Object {$_.Name -like "*windows*ai*"}

# Kill processes
Stop-Process -Name "windows-ai*" -Force
```

**2. Stop Windows Service**
```
Win+R → services.msc
Find "WindowsAI"
Right-click → Stop
```

**3. Clean Previous Installation**
```
Delete: C:\Program Files\Windows AI
Delete: %APPDATA%\WindowsAI
Restart computer
Try installation again
```

### Installation Hangs/Freezes

**Symptoms:**
- Installer stuck at certain percentage
- "Not Responding" in Task Manager
- Progress bar doesn't move

**Solutions:**

**1. Wait Longer**
- Python dependency installation can take 2-5 minutes
- Node.js dependencies take 1-2 minutes
- Don't interrupt during these stages

**2. Check Logs**
```
Location: %TEMP%\WindowsAI-Install.log
Open with Notepad
Look for errors
```

**3. Cancel and Retry**
- Close installer
- Delete partial installation:
  ```
  C:\Program Files\Windows AI
  %APPDATA%\WindowsAI
  ```
- Run installer again

**4. Disable Network**
- Disconnect internet temporarily
- Prevents installer from downloading updates
- Use offline installation

---

## Startup Problems

### App Won't Start After Installation

**Symptoms:**
- Icon appears in taskbar briefly then disappears
- No window opens
- Silent failure

**Diagnostic Steps:**

**1. Check if Process is Running**
```powershell
Get-Process | Where-Object {$_.Name -like "*electron*"}
Get-Process | Where-Object {$_.ProcessName -eq "windows-ai"}
```

**2. Check Backend Service**
```
Win+R → services.msc
Find "WindowsAI"
Status should be "Running"
```

**3. Test Backend Manually**
```
Open browser
Go to: http://localhost:8010/health
Should see: {"status": "healthy"}
```

**Solutions:**

**1. Restart Windows Service**
```
services.msc → WindowsAI → Restart
```

**2. Check Port Availability**
```powershell
# Check if port 8010 is in use
netstat -ano | findstr :8010

# Kill process using port (if needed)
taskkill /F /PID <PID>
```

**3. Run from Command Line**
```powershell
cd "C:\Program Files\Windows AI"
.\apps\gui\windows-ai-gui.exe
# Look for error messages
```

**4. Check Logs**
```
%APPDATA%\WindowsAI\logs\app.log
%APPDATA%\WindowsAI\logs\backend.log
```

### Crash on Startup

**Symptoms:**
- App starts then crashes
- Error message displayed
- Event Viewer shows application error

**Solutions:**

**1. Check Event Viewer**
```
Win+R → eventvwr
Windows Logs → Application
Look for "WindowsAI" errors
```

**2. Reset Configuration**
```powershell
# Backup config
Copy-Item "%APPDATA%\WindowsAI\config.json" "%APPDATA%\WindowsAI\config.json.bak"

# Delete config (will be recreated with defaults)
Remove-Item "%APPDATA%\WindowsAI\config.json"

# Restart app
```

**3. Update Graphics Drivers**
- Electron requires modern graphics drivers
- Visit GPU manufacturer website:
  - NVIDIA: https://www.nvidia.com/drivers
  - AMD: https://www.amd.com/support
  - Intel: https://www.intel.com/content/www/us/en/download-center

**4. Disable GPU Acceleration**

Edit `%APPDATA%\WindowsAI\config.json`:
```json
{
  "disable_gpu": true
}
```

**5. Safe Mode Start**
```powershell
cd "C:\Program Files\Windows AI"
.\apps\gui\windows-ai-gui.exe --safe-mode
```

---

## Backend/Service Issues

### Backend Shows "Offline"

**Symptoms:**
- Red "Offline" indicator in GUI
- Chat doesn't work
- API calls fail

**Diagnostic Steps:**

**1. Check Service Status**
```
Win+R → services.msc
Find "WindowsAI"
Note the status and startup type
```

**2. Test Backend Directly**
```
curl http://localhost:8010/health
# Or open in browser
```

**3. Check Process**
```powershell
Get-Process -Name "python" | Where-Object {$_.CommandLine -like "*windows_ai*"}
```

**Solutions:**

**1. Restart Service**
```powershell
# Stop service
net stop WindowsAI

# Start service
net start WindowsAI
```

**2. Check Service Logs**
```
%APPDATA%\WindowsAI\logs\service.log
%APPDATA%\WindowsAI\logs\backend.log
```

**3. Reinstall Service**
```powershell
cd "C:\Program Files\Windows AI\install"

# Remove service
python windows_service.py remove

# Install service
python windows_service.py --startup auto install

# Start service
net start WindowsAI
```

**4. Run Backend Manually (for debugging)**
```powershell
cd "C:\Program Files\Windows AI"
.\python\python.exe -m windows_ai.main
# Check console output for errors
```

### Service Won't Start

**Symptoms:**
- "Could not start WindowsAI service" error
- Service status: Stopped
- Error 1053: "Service did not respond in a timely fashion"

**Solutions:**

**1. Check Service Configuration**
```
services.msc → WindowsAI → Properties
Log On tab: Should be "Local System account"
```

**2. Check Dependencies**
```powershell
cd "C:\Program Files\Windows AI"
.\python\python.exe -m pip list
# Verify all required packages installed
```

**3. Check Python Installation**
```powershell
cd "C:\Program Files\Windows AI"
.\python\python.exe --version
# Should output: Python 3.11.x
```

**4. Check Permissions**
```
Right-click: C:\Program Files\Windows AI
Properties → Security
"SYSTEM" should have full control
```

**5. Re-register Service**
```powershell
cd "C:\Program Files\Windows AI\install"

# Unregister
python windows_service.py remove

# Delete old service registry
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\WindowsAI" /f

# Register fresh
python windows_service.py --startup auto install
```

---

## Model Download Problems

### Model Download Fails

**Symptoms:**
- "Download failed" error
- Download stuck at 0% or certain percentage
- Network error messages

**Solutions:**

**1. Check Internet Connection**
```powershell
# Test connectivity to Ollama
Test-NetConnection -ComputerName ollama.ai -Port 443

# Test general connectivity
ping 8.8.8.8
```

**2. Check Disk Space**
```powershell
# Check available space
Get-PSDrive C | Select-Object Used,Free
# Need at least 5-10 GB free
```

**3. Check Firewall**
```
Windows Defender Firewall
→ Allow an app through firewall
→ Find "ollama.exe" or "Windows AI"
→ Enable for Private and Public
```

**4. Retry Download**
- Close and reopen Windows AI
- Try downloading again
- Downloads resume from where they stopped

**5. Manual Download**
```powershell
cd "C:\Program Files\Windows AI"
.\ollama.exe pull llama2
```

**6. Use Different Model**
- Try smaller model first (mistral vs llama2:70b)
- Verify working download system
- Then try larger models

### Model Download is Very Slow

**Causes:**
- Large model size (4-40 GB)
- Slow internet connection
- Server congestion

**Solutions:**

**1. Check Download Speed**
```powershell
# Test internet speed
speedtest-cli
# Or visit: https://fast.com
```

**2. Download During Off-Peak Hours**
- Night/early morning usually faster
- Less server load

**3. Pause Other Downloads**
- Windows Update
- Cloud sync (OneDrive, Dropbox)
- Streaming services

**4. Estimated Times**

| Model Size | 10 Mbps | 50 Mbps | 100 Mbps |
|------------|---------|---------|----------|
| 4 GB | 53 min | 11 min | 5 min |
| 7 GB | 93 min | 19 min | 9 min |
| 13 GB | 173 min | 35 min | 17 min |

---

## Chat/AI Issues

### Chat Responses are Slow

**Symptoms:**
- Long wait for AI responses
- Typing indicator shows for minutes
- Delayed text generation

**Causes & Solutions:**

**1. Large Model on Slow Hardware**
```
Solution: Use smaller/faster model
Settings → Models → Switch to:
- mistral (faster)
- llama2:7b (instead of 13b or 70b)
```

**2. Insufficient RAM**
```powershell
# Check RAM usage
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10

# If RAM > 90%:
- Close other applications
- Use smaller model
- Increase system RAM
```

**3. CPU Bottleneck**
```
Settings → Advanced
→ CPU Threads: Limit to 4 or 6
(Prevents maxing out CPU)
```

**4. Disk I/O**
- Models on slow HDD?
- Move to SSD:
  ```
  Settings → Models → Download Location
  Choose SSD drive
  Re-download models
  ```

### Chat Responses are Nonsensical

**Symptoms:**
- Gibberish output
- Repetitive text
- Irrelevant responses

**Solutions:**

**1. Adjust Temperature**
```
Chat Settings (⚙️)
→ Temperature: 0.7 (default)
Lower = more focused (0.3-0.5)
Higher = more creative (0.8-1.0)
```

**2. Reset Conversation**
```
Click 🔄 New Chat
Previous context may have confused model
```

**3. Try Different Model**
```
Switch to different model
Some models better at certain tasks
```

**4. Improve Prompt**
```
Bad: "files"
Good: "List all PDF files in my Downloads folder"

Bad: "fix it"
Good: "Fix the syntax error in myfile.py on line 42"
```

**5. Clear Model Cache**
```powershell
cd "C:\Program Files\Windows AI"
.\ollama.exe rm llama2  # Remove model
.\ollama.exe pull llama2  # Re-download
```

### Chat Doesn't Respond at All

**Symptoms:**
- Message sent but no response
- Spinning indicator forever
- "Backend offline" error

**Diagnostic:**

**1. Check Backend**
```
Open browser: http://localhost:8010/health
If error: Backend is offline (see Backend Issues section)
```

**2. Check Model Status**
```
Models tab
Verify model is downloaded and active
```

**3. Check Logs**
```
%APPDATA%\WindowsAI\logs\chat.log
%APPDATA%\WindowsAI\logs\ollama.log
```

**Solutions:**

**1. Restart Backend**
```
services.msc → WindowsAI → Restart
```

**2. Reload Model**
```
Models tab
Delete model
Re-download model
Set as default
```

**3. Clear Chat Cache**
```powershell
Remove-Item "%APPDATA%\WindowsAI\chat-cache" -Recurse -Force
```

---

## Automation Problems

### Folder Watcher Not Working

**Symptoms:**
- Files added but not detected
- Rules don't trigger
- Watcher shows "Active" but doesn't act

**Diagnostic Steps:**

**1. Check Watcher Status**
```
Automation tab
Watcher should show green "Active"
Check "Last run" timestamp
```

**2. Test Manually**
```
Add test file to watched folder
Wait 10-30 seconds
Check if rule triggered
```

**Solutions:**

**1. Increase Check Interval**
```
Settings → Automation
→ Watcher Check Interval: 5s → 10s
Sometimes 1s is too aggressive
```

**2. Check Folder Permissions**
```
Right-click watched folder
→ Properties → Security
"SYSTEM" needs Read access
```

**3. Verify Folder Path**
```
Automation tab → Edit Watcher
Verify folder path is correct
Try absolute path: C:\Users\...\Downloads
```

**4. Restart Watchers**
```
Automation tab
Disable all watchers
Re-enable watchers
```

**5. Check Logs**
```
%APPDATA%\WindowsAI\logs\automation.log
Look for watcher errors
```

### Scheduled Task Not Running

**Symptoms:**
- Task shows "Enabled" but doesn't run
- Missed scheduled time
- No execution history

**Solutions:**

**1. Check Next Run Time**
```
Automation tab → Scheduled Tasks
Verify "Next run" is in the future
If in past, task may have failed
```

**2. Run Task Manually**
```
Find task
Click [Run Now]
Check if executes successfully
```

**3. Check Schedule Format**
```
Examples of valid schedules:
- "Every day at 3:00 PM"
- "Every Monday at 9:00 AM"
- "1st of every month at 12:00 PM"

Invalid:
- "daily 3pm" (too vague)
- "Mondays" (no time specified)
```

**4. Check Task Permissions**
```
If task needs admin privileges:
Edit task → Run as Administrator
```

**5. Check Task Logs**
```
%APPDATA%\WindowsAI\logs\tasks.log
Shows execution history and errors
```

---

## Plugin Issues

### Plugin Won't Install

**Symptoms:**
- "Installation failed" error
- Plugin doesn't appear in list
- Permission errors

**Solutions:**

**1. Check Plugin Compatibility**
```
Plugin must specify: min_app_version
Check if compatible with your version:
Help → About → Version
```

**2. Check Dependencies**
```
Plugins may require Python packages
Check plugin README for requirements
Install manually if needed:
cd "C:\Program Files\Windows AI"
.\python\python.exe -m pip install <package>
```

**3. Install from File**
```
If installing from .zip:
1. Extract .zip first
2. Verify folder structure
3. Install extracted folder
```

**4. Check Permissions**
```
%APPDATA%\WindowsAI\plugins\
Folder must be writable
```

**5. Install Manually**
```
Copy plugin folder to:
%APPDATA%\WindowsAI\plugins\custom\
Restart Windows AI
```

### Plugin Not Working After Install

**Symptoms:**
- Plugin shows "Installed" but doesn't function
- Commands not recognized
- Plugin errors

**Solutions:**

**1. Enable Plugin**
```
Plugins tab
Find plugin
Click [Enable]
Green checkmark should appear
```

**2. Configure Plugin**
```
Click [Configure]
Fill in required settings (API keys, etc.)
Save configuration
```

**3. Check Plugin Logs**
```
%APPDATA%\WindowsAI\logs\plugins.log
%APPDATA%\WindowsAI\plugins\<plugin_name>\plugin.log
```

**4. Reinstall Plugin**
```
Uninstall plugin
Restart app
Install plugin again
```

---

## Performance Problems

### High RAM Usage

**Symptoms:**
- Windows AI using 4+ GB RAM
- System sluggish
- Out of memory errors

**Causes:**

1. **Large AI Model**
   - llama2:70b uses 40+ GB RAM
   - llama2:13b uses 8-10 GB RAM

2. **Multiple Models Loaded**
   - Each active model uses RAM

3. **Memory Leaks**
   - Long-running sessions
   - Many chat conversations

**Solutions:**

**1. Use Smaller Model**
```
Models tab
Switch from 13b/70b to 7b
llama2:7b uses ~4-6 GB RAM
```

**2. Limit RAM Usage**
```
Settings → Advanced
→ Max RAM Usage: 4 GB
Model will use swap if needed (slower but won't crash)
```

**3. Restart Application**
```
Close Windows AI
Wait 10 seconds
Reopen
Frees up leaked memory
```

**4. Clear Chat History**
```
Settings → Privacy
→ Clear All Chat Data
Old conversations can consume RAM
```

**5. Close Other Applications**
```
Free up system RAM
Check Task Manager for memory hogs
```

### High CPU Usage

**Symptoms:**
- Windows AI using 100% CPU
- Fan running loud
- System overheating

**Solutions:**

**1. Limit CPU Threads**
```
Settings → Advanced
→ CPU Threads: 4 (or 50% of total cores)
```

**2. Lower Model Priority**
```powershell
# In Task Manager
Find "ollama.exe" process
Right-click → Set Priority → Below Normal
```

**3. Pause Watchers**
```
Automation tab
Disable folder watchers temporarily
Re-enable when not doing intensive work
```

**4. Check for Runaway Processes**
```powershell
Get-Process | Sort-Object CPU -Descending
# Look for unexpected high CPU processes
```

---

## Network/Connectivity Issues

### Cannot Connect to Backend

**Symptoms:**
- "Backend offline" persistent
- http://localhost:8010 doesn't work
- Connection refused errors

**Solutions:**

**1. Check if Port is Listening**
```powershell
netstat -ano | findstr :8010
# Should see LISTENING
```

**2. Check Firewall Rules**
```
Windows Defender Firewall
→ Advanced settings
→ Inbound Rules
→ Find "Windows AI" or port 8010
→ Ensure "Allow" action
```

**3. Try Different Port**
```
Edit %APPDATA%\WindowsAI\config.json:
{
  "backend_port": 8011
}
Restart app
```

**4. Check for Port Conflicts**
```powershell
# See what's using port 8010
netstat -ano | findstr :8010

# Kill conflicting process
taskkill /F /PID <PID>
```

---

## Uninstallation Issues

### Uninstaller Doesn't Remove Everything

**What Gets Left Behind:**

By design (user data):
```
%APPDATA%\WindowsAI\        - User data, settings, chats
%LOCALAPPDATA%\WindowsAI\   - Cache, temp files
```

Should be removed:
```
C:\Program Files\Windows AI\  - Application files
Registry: HKLM\Software\Windows AI
Start Menu shortcuts
```

**Manual Cleanup:**

**1. Remove Application Files**
```powershell
Remove-Item "C:\Program Files\Windows AI" -Recurse -Force
```

**2. Remove User Data (if desired)**
```powershell
Remove-Item "$env:APPDATA\WindowsAI" -Recurse -Force
Remove-Item "$env:LOCALAPPDATA\WindowsAI" -Recurse -Force
```

**3. Remove Registry Keys**
```powershell
reg delete "HKLM\Software\Windows AI" /f
reg delete "HKCU\Software\Windows AI" /f
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\Windows AI" /f
```

**4. Remove Service**
```powershell
sc delete WindowsAI
```

**5. Remove Shortcuts**
```powershell
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Windows AI" -Recurse -Force
Remove-Item "$env:USERPROFILE\Desktop\Windows AI.lnk" -Force
```

---

## Log Files

### Where to Find Logs

```
Application Logs:
%APPDATA%\WindowsAI\logs\app.log
%APPDATA%\WindowsAI\logs\electron.log

Backend Logs:
%APPDATA%\WindowsAI\logs\backend.log
%APPDATA%\WindowsAI\logs\service.log

AI Model Logs:
%APPDATA%\WindowsAI\logs\ollama.log
%APPDATA%\WindowsAI\logs\model.log

Automation Logs:
%APPDATA%\WindowsAI\logs\automation.log
%APPDATA%\WindowsAI\logs\watchers.log

Plugin Logs:
%APPDATA%\WindowsAI\logs\plugins.log
```

### How to Read Logs

**1. Open Log File**
```powershell
notepad "%APPDATA%\WindowsAI\logs\app.log"
```

**2. Look for Errors**
```
Search for: "ERROR", "EXCEPTION", "FAILED"
Note timestamp and error message
```

**3. Check Recent Entries**
```powershell
# View last 50 lines
Get-Content "%APPDATA%\WindowsAI\logs\app.log" -Tail 50
```

**4. Filter by Date**
```powershell
# Today's logs only
Get-Content "%APPDATA%\WindowsAI\logs\app.log" | Select-String (Get-Date -Format "yyyy-MM-dd")
```

### Enable Debug Logging

For more detailed logs:

```
Settings → Advanced
→ Debug Mode: Enabled
→ Log Level: DEBUG

Restart application
Logs will be much more verbose
```

---

## Getting Help

### Before Asking for Help

**1. Check Documentation**
- [Quick Start](QUICK_START.md)
- [User Guide](USER_GUIDE.md)
- [FAQ](FAQ.md)
- This troubleshooting guide

**2. Search Existing Issues**
- GitHub Issues: https://github.com/yourorg/Windows-AI/issues
- Check if your problem already reported

**3. Gather Information**
- Windows version: `Win+R → winver`
- App version: Help → About
- Error logs: `%APPDATA%\WindowsAI\logs\`

### Reporting Issues

**What to Include:**

1. **Description**
   - What you were trying to do
   - What happened instead
   - What you expected to happen

2. **Steps to Reproduce**
   ```
   1. Open Windows AI
   2. Go to Chat tab
   3. Type "test command"
   4. Error appears
   ```

3. **Environment**
   - Windows version
   - Windows AI version
   - System specs (RAM, CPU)

4. **Logs**
   - Relevant log excerpts
   - Full logs if possible

5. **Screenshots**
   - Error messages
   - Unexpected behavior

### Where to Get Help

**Community Support:**
- GitHub Issues: Bug reports
- GitHub Discussions: Questions and answers
- Discord: Real-time help
- Reddit: r/WindowsAI

**Documentation:**
- User Guide: Complete feature docs
- FAQ: Common questions
- API Reference: For developers

---

*Last updated: 2025-01-10 | Windows AI v0.5.0*
