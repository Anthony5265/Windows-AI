# Task 31: Explorer Context Menu

**Goal**: Right‑click → “Run with Windows AI” for files/folders.

**Scope**
- Modern context menu via IExplorerCommand (with app identity) when supported
- Classic fallback via registry verbs under HKCU for Files & Directory
- Commands: Summarize, Extract Data, Rename via Pattern, Send to Agent
- Pass absolute paths to Actions API; multi‑select support

**Acceptance**
- Menu appears on Win11; “Show more options” fallback works on older builds
- Multi‑select passes all paths; sample actions succeed
- Uninstaller removes all menu entries
