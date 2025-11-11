# Automation UI - User Guide

Complete guide to using Windows-AI's automation features through the graphical user interface.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Folder Watchers](#folder-watchers)
4. [Scheduled Tasks](#scheduled-tasks)
5. [Workflow Templates](#workflow-templates)
6. [Execution History](#execution-history)
7. [Statistics Dashboard](#statistics-dashboard)
8. [Best Practices](#best-practices)

## Overview

The Automation UI provides a visual interface for creating and managing automated workflows in Windows-AI. You can:

- **Monitor folders** for file changes and trigger AI actions
- **Schedule tasks** to run at specific times or intervals
- **Use pre-built templates** for common automation scenarios
- **View execution history** to track automation performance
- **Monitor statistics** to understand automation effectiveness

## Getting Started

### Accessing the Automation Tab

1. Launch Windows-AI
2. Click the **Automation** tab in the main navigation
3. You'll see sections for:
   - Folder Watchers
   - Scheduled Tasks
   - Workflow Templates
   - Execution History
   - Statistics

### Interface Overview

- **Add Buttons**: Create new automations (+ Add Watcher, + Add Task)
- **Automation Cards**: View and manage existing automations
- **Status Badges**: Green = Active, Gray = Inactive
- **Action Buttons**: Play/Pause and Delete controls
- **Filters**: Sort and filter execution history

## Folder Watchers

### What are Folder Watchers?

Folder watchers monitor specified directories for file changes and automatically trigger AI actions when events occur.

### Creating a Folder Watcher

1. Click **+ Add Watcher**
2. Fill in the configuration form:

**Basic Settings:**
- **Name**: Descriptive name (e.g., "Downloads Organizer")
- **Folder Path**: Directory to monitor (e.g., `C:\Users\YourName\Downloads`)
- **File Patterns**: Comma-separated patterns (e.g., `*.pdf, *.docx, *.txt`)
  - Use `*.*` to watch all files
  - Use specific extensions like `*.jpg, *.png` for images

**Events to Watch:**
- ☑ **Created**: Trigger when new files are created
- ☐ **Modified**: Trigger when files are modified
- ☐ **Deleted**: Trigger when files are deleted

**AI Action:**
- **Organize Files**: Automatically organize files into folders
- **Summarize Content**: Create summaries of file contents
- **Analyze File**: Deep analysis of file contents
- **Custom**: Use your own AI prompt

**Custom Prompt** (optional):
- Provide specific instructions for the AI
- Example: "Organize this file into a subfolder based on its type"

3. Click **Save Watcher**

### Example Use Cases

#### Download Organizer
```
Name: Downloads Organizer
Path: ~/Downloads
Patterns: *.*
Events: Created
Action: Organize
Prompt: Sort this file into Documents, Images, Videos, or Archives folder
```

#### Screenshot OCR
```
Name: Screenshot Text Extractor
Path: ~/Pictures/Screenshots
Patterns: *.png, *.jpg
Events: Created
Action: Analyze
Prompt: Extract text from this screenshot and save to a text file
```

#### Log Monitor
```
Name: Error Log Watcher
Path: /var/log
Patterns: *.log
Events: Modified
Action: Analyze
Prompt: Check for errors or warnings and alert if critical issues found
```

### Managing Watchers

- **▶ Play**: Start monitoring (watcher becomes active)
- **⏸ Pause**: Stop monitoring (watcher remains configured but inactive)
- **🗑 Delete**: Permanently remove the watcher

## Scheduled Tasks

### What are Scheduled Tasks?

Scheduled tasks run AI actions automatically at specified times or intervals.

### Creating a Scheduled Task

1. Click **+ Add Task**
2. Fill in the configuration form:

**Basic Settings:**
- **Name**: Task name (e.g., "Daily Briefing")
- **Description**: What the task does

**Schedule Configuration:**
- **Schedule Type**:
  - **Interval**: Run every X minutes/hours/days (e.g., `1h`, `30m`, `2d`)
  - **Cron**: Advanced scheduling (e.g., `0 9 * * *` = 9 AM daily)
  - **Once**: Run one time only (specify datetime)

**Schedule Examples:**
- `30m` - Every 30 minutes
- `2h` - Every 2 hours
- `1d` - Once per day
- `0 9 * * *` - 9 AM every day (cron)
- `0 */2 * * *` - Every 2 hours (cron)
- `0 0 * * 0` - Midnight every Sunday (cron)

**AI Action:**
- **Summarize**: Create summaries
- **System Check**: Check system status
- **Backup**: Backup files
- **Cleanup**: Clean temporary files
- **Custom**: Your own action

**AI Prompt:**
- Detailed instructions for what the task should do
- Example: "Provide a daily briefing with weather, news, and calendar"

3. Click **Save Task**

### Example Use Cases

#### Daily Morning Briefing
```
Name: Daily Briefing
Description: Morning summary of tasks and calendar
Schedule: 0 9 * * * (9 AM every day)
Action: Summarize
Prompt: Provide today's weather, top news, and calendar appointments
```

#### Weekly Backup
```
Name: Weekly Backup
Description: Backup important files
Schedule: 0 2 * * 0 (2 AM every Sunday)
Action: Backup
Prompt: Backup Documents and Pictures folders, report space used
```

#### Hourly Log Check
```
Name: Log Analyzer
Description: Check logs for errors
Schedule: 0 * * * * (Every hour)
Action: System Check
Prompt: Analyze system logs for critical errors and alert if found
```

### Managing Tasks

- **▶ Enable**: Activate the scheduled task
- **⏸ Disable**: Deactivate (task remains but won't run)
- **🗑 Delete**: Permanently remove the task

## Workflow Templates

### What are Templates?

Pre-configured automation templates for common use cases. One-click setup!

### Available Templates

1. **📁 Download Organizer**
   - Automatically organize downloads by file type
   - Sorts into Documents, Images, Videos, etc.

2. **📰 Daily Briefing**
   - Morning summary of calendar and tasks
   - Runs at 9 AM every day

3. **💾 Backup Automation**
   - Scheduled backup of important folders
   - Runs at 2 AM daily

4. **📸 Screenshot OCR**
   - Auto-organize and extract text from screenshots
   - Uses AI to extract text content

5. **📊 Log Analyzer**
   - Parse and alert on error logs
   - Monitors system logs continuously

6. **🧹 Disk Cleanup**
   - Automated temp file cleanup
   - Runs weekly on Sundays

### Using a Template

1. Scroll to **Workflow Templates** section
2. Click **Use Template** on the desired template
3. Review the pre-filled configuration
4. Customize as needed (paths, prompts, schedule)
5. Click **Save**

The template automatically fills in all settings - you just need to verify and adjust for your system!

## Execution History

### Viewing History

The **Execution History** section shows a timeline of all automation executions.

### History Information

Each entry shows:
- **Icon**: 📁 (Watcher) or ⏰ (Task)
- **Name**: Automation that ran
- **Status**: ✅ Success or ❌ Error
- **Timestamp**: When it executed
- **Duration**: How long it took
- **Message**: Result or error description

### Filtering History

**Filter by Type:**
- All Automations
- Watchers Only
- Tasks Only

**Filter by Status:**
- All Status
- Success Only
- Errors Only

### Clearing History

Click **Clear History** to remove all execution records. This action cannot be undone!

## Statistics Dashboard

### Available Metrics

📊 **Total Automations**
- Total number of watchers + tasks configured
- Shows overall automation coverage

📊 **Active Now**
- Currently running watchers + enabled tasks
- Indicates active automation count

📊 **Executions Today**
- Number of automation runs since midnight
- Tracks daily activity level

📊 **Success Rate**
- Percentage of successful executions
- Monitors automation reliability

### Using Statistics

- **High Success Rate** (>90%): Automations working well
- **Low Success Rate** (<80%): Review error logs, fix issues
- **High Executions**: Frequent automation activity
- **Low Executions**: Check if automations are enabled

## Real-time Updates

The automation UI automatically refreshes every 5 seconds when the tab is open, showing:

- ✅ New watcher detections
- ✅ Task execution completions
- ✅ Status changes (active/inactive)
- ✅ Updated statistics
- ✅ Latest execution history

## Best Practices

### Folder Watchers

1. **Use Specific Patterns**: Instead of `*.*`, use `*.pdf, *.docx` to reduce noise
2. **Avoid System Folders**: Don't watch `/System` or `/Windows` directories
3. **Test with One File**: Create a watcher, test with one file, then enable fully
4. **Use Recursive Carefully**: Only enable for shallow directory trees

### Scheduled Tasks

1. **Test Prompts First**: Run your AI prompt manually before scheduling
2. **Avoid Overlaps**: Don't schedule tasks too frequently that they overlap
3. **Use Cron for Precision**: Use cron syntax for exact times (e.g., 9 AM sharp)
4. **Monitor First Runs**: Check execution history after first few runs

### General Tips

1. **Start Small**: Begin with 1-2 automations, expand gradually
2. **Monitor History**: Check execution history weekly for errors
3. **Update Prompts**: Refine AI prompts based on results
4. **Use Templates**: Start with templates, customize later
5. **Check Statistics**: Review success rate monthly
6. **Clean Up**: Delete unused automations to reduce clutter

## Troubleshooting

### Watcher Not Triggering

**Problem**: Files added to folder but watcher doesn't react

**Solutions**:
1. Check watcher status (must be Active/Green)
2. Verify file patterns match your files
3. Ensure events are checked (Created, Modified, etc.)
4. Check folder path is correct
5. Look for errors in execution history

### Task Not Running

**Problem**: Scheduled task doesn't execute at expected time

**Solutions**:
1. Verify task is Enabled (green badge)
2. Check schedule syntax (cron or interval)
3. Look at "Next run" time in task card
4. Review execution history for errors
5. Ensure backend is running

### Low Success Rate

**Problem**: Many failed executions in history

**Solutions**:
1. Review error messages in execution history
2. Test AI prompts manually in chat
3. Check file/folder permissions
4. Verify paths exist and are accessible
5. Simplify complex prompts

### Backend Not Responding

**Problem**: Can't create automations, interface not loading

**Solutions**:
1. Check backend status at bottom of window
2. Restart Windows-AI backend (`python -m windows_ai.main`)
3. Verify backend URL is `http://localhost:8010`
4. Check firewall isn't blocking connection

## Keyboard Shortcuts

- `Ctrl/Cmd + N`: New automation (context-dependent)
- `Ctrl/Cmd + R`: Refresh automation list
- `Ctrl/Cmd + H`: Toggle execution history
- `Delete`: Delete selected automation
- `Space`: Toggle active/inactive

## Advanced Features

### Custom AI Prompts

Get the most out of automations with powerful prompts:

**File Organization:**
```
Analyze this file's content and metadata. Organize it into:
- Documents/Work for work-related files
- Documents/Personal for personal files
- Archives for old files (>1 year)
Create appropriate subfolders as needed.
```

**Smart Summarization:**
```
Read this file and create:
1. A 2-sentence summary
2. Key points (bullet list)
3. Action items if any
Save summary as [original_name]_summary.txt
```

**Intelligent Backup:**
```
Backup the following directories to external drive:
- ~/Documents/Important
- ~/Projects/Active
Skip files larger than 100MB.
Report total size and file count.
```

### Multiple Watchers

You can create multiple watchers for the same folder with different patterns:

- Watcher 1: `*.pdf` → Organize into Documents
- Watcher 2: `*.jpg, *.png` → Organize into Images
- Watcher 3: `*.mp4, *.avi` → Organize into Videos

### Chaining Automations

Use one automation to trigger another:

1. **Watcher**: Downloads folder → Organize files
2. **Watcher**: Organized folder → Summarize content
3. **Task**: Daily summary of all summaries

## FAQ

**Q: Can I use automations offline?**
A: Watchers and tasks can run offline for local file operations, but AI actions require internet for cloud models (or local models with Ollama).

**Q: How many automations can I create?**
A: No hard limit, but we recommend <20 for performance. More automations = more background monitoring.

**Q: Do automations run when Windows-AI is closed?**
A: No, the backend must be running for automations to work. Consider setting up Windows-AI to auto-start.

**Q: Can I export/import automations?**
A: Not yet in the UI, but configuration files are stored in `~/.windows-ai/watchers.json` and `~/.windows-ai/scheduler.json` and can be manually backed up.

**Q: What happens if two watchers trigger on the same file?**
A: Both will execute independently. Use specific patterns to avoid conflicts.

**Q: Can I schedule tasks to run on specific days?**
A: Yes! Use cron syntax:
- `0 9 * * 1` - Mondays at 9 AM
- `0 17 * * 5` - Fridays at 5 PM
- `0 12 * * 0,6` - Weekends at noon

**Q: How do I stop all automations quickly?**
A: Click the pause button (⏸) on each watcher/task, or restart the backend.

## Support & Resources

- **Documentation**: `/docs/automation_builder.md` (technical details)
- **API Reference**: `/docs/API.md` (for developers)
- **Examples**: See Workflow Templates for inspiration
- **GitHub Issues**: Report bugs or request features
- **Community**: Share your automation workflows!

---

**Last Updated**: 2025-11-10
**Version**: 2.0
