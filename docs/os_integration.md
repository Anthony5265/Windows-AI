# Operating System Integration

This project showcases several examples of how Windows AI features may
hook into operating system components:

* **Explorer integration** – `windows_ai.explorer` can reason about
  files in a folder and suggest clean up operations.
* **Task Manager integration** – `windows_ai.task_manager` performs
  lightweight analysis of running processes.
* **Context menu hooks** – registry scripts in `install/` allow adding an
  "Ask Windows AI" entry to the Windows right‑click menu.  The toggle for
  this feature is exposed through `control_center.backends`.
* **GUI overlays and hotkeys** – `gui.core` includes an overlay system
  and a simple hotkey manager that can be extended by higher level
  applications.

These modules provide isolated, testable building blocks intended to be
wired into real Windows APIs by downstream packages.
