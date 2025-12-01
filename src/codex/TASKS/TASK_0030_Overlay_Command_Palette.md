# Task 30: Overlay / Command Palette

**Goal**: Fast overlay to run actions, workflows, and agents anywhere.

**Scope**
- Fuzzy search over Actions, Workflows, Agents, Files
- Parameter form for a workflow; preview result
- Render markdown; copy to clipboard; insert to focused app (SendKeys)

**Acceptance**
- Search returns results <150ms on 1k items
- Running a sample workflow produces expected output and toast
- Escape closes overlay; re‑opens instantly
