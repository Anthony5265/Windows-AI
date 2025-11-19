# Windows AI — MEGA PROMPT for Codex

Read `codex/manifest.json` → open the file in `"entry"`. Load `codex/STATE.json`.

──────────────────────────────────────────────────────────────────────────────
0) PERMISSIONS & SCOPE (READ THIS FIRST)
──────────────────────────────────────────────────────────────────────────────
• You (Codex) have explicit authorization to go very far to complete this repo.
• The user will supply a **fine-grained GitHub Personal Access Token (PAT)** that grants broad read/write on issues, PRs, code, workflows, pages, environments, statuses, secrets, etc.
• DO NOT echo, log, or commit any token. If you must display it, mask everything except the last 4 characters.
• Prefer branches + PRs and keep CI green. If pushing is blocked at any time, produce a full **patch ZIP** (Base64) for manual upload and STOP.

──────────────────────────────────────────────────────────────────────────────
1) GIT REMOTE & BRANCH SETUP
──────────────────────────────────────────────────────────────────────────────
# Fill in the placeholder before running:
#   TOKEN=<YOUR_GITHUB_PAT>
# If you cannot push, skip to §11 (NO-REMOTE fallback).

SH:
  set -e
  TOKEN="${TOKEN:-<YOUR_GITHUB_PAT>}"               # <— user replaces
  git init 2>/dev/null || true
  git config user.name  "Anthony"
  git config user.email "anthonybone5265@gmail.com"
  if [ -z "$(git config --get remote.origin.url)" ]; then
    URL="https://${TOKEN:+x-access-token:${TOKEN}@}github.com/Anthony5265/Windows-AI.git"
    git remote add origin "$URL" 2>/dev/null || git remote set-url origin "$URL"
  fi
  git fetch origin || true
  git checkout -B main || true
  git pull --rebase origin main || true

──────────────────────────────────────────────────────────────────────────────
2) OPERATING RULES
──────────────────────────────────────────────────────────────────────────────
• Always consult `codex/STATE.json` for TODOs.
• Use Conventional Commits.
• Keep these contracts stable unless updated in the spec:
  - Actions API: POST /api/actions/execute
  - AgentHub:   POST /workflows/run
  - Proxy:      OpenAI /v1/chat/completions (configured by config/proxy.yaml)
• Log JSONL to `C:\Windows AI\logs\<service>\*.log`.
• Default prefixes under `C:\Windows AI\…` (configurable in Settings).

──────────────────────────────────────────────────────────────────────────────
3) EPIC A — GUI OVERHAUL (premium visuals, 60fps)
──────────────────────────────────────────────────────────────────────────────
Branch: `feature/gui-overhaul`  → open PR when ready.

Goal: Elevate Electron GUI to a premium, responsive experience without hurting performance.

Requirements
• Fluent-like spacing/typography with lightweight components.
• Global theming: dark/light + high-contrast; persist per user.
• Motion at 60fps: CSS transforms + requestAnimationFrame; avoid layout thrash.
• Chat: streaming bubbles; markdown + code-block copy; retry/edit; tool-call inspector.
• Models: richer cards (memory/disk, VRAM hint, est. tokens/sec from recent runs).
• Settings: search across all settings; one-click “Reset to defaults”.
• Terminal: polish tabs/splits; theme preview; keybinding editor UI.
• Logs/Jobs: filter by service/job; live tail; export to JSONL.

Non-goals
• Heavy 3D shaders; theme marketplaces.

Quality gates
• Renderer perf budget: cold-start TTI < 2.5s.
• Unit tests: theme persistence + settings search.
• Playwright E2E: launch → switch theme → open chat → send/stream → open Terminal → run workflow.

Commit style: `feat(gui): …`  
STATE: add “GUI Overhaul” checklist and tick items as delivered.

──────────────────────────────────────────────────────────────────────────────
4) EPIC B — SETUP AGENT (first-run wizard that installs & validates itself)
──────────────────────────────────────────────────────────────────────────────
Branch: `feature/setup-agent`  → open PR.

Create module/service `setup-agent`.

Flow
1) Detect CPU/GPU, RAM, disk, Windows version, admin rights, firewall rules.
2) Recommend local model+quant (e.g., phi3, mistral) with est. tokens/sec + disk usage.
3) One-click install Ollama if missing; download model; warm cache.
4) Configure LiteLLM Proxy logical names; test `/v1/chat/completions`.
5) Verify Actions API + AgentHub health; auto-fix missing prereqs (mkcert optional).
6) Create a restore point (config backup) and rollback plan.
7) Smoke test: chat “hello”; run System Info workflow; write a file via Actions API.
8) Human-readable report + JSON diagnostics at `logs/setup-agent.json`.

UX
• Stepper with progress, ETA, “Why this?” tooltips. Skip/advanced toggles. Reversible.

Quality gates
• Unit tests: hardware detection, model recommendation, config writer.
• E2E: headless first-run validates services and writes the report.

Commits: `feat(setup-agent): …`

──────────────────────────────────────────────────────────────────────────────
5) EPIC C — SELF-HEALING & AUTO-ROLLBACK
──────────────────────────────────────────────────────────────────────────────
Branch: `feature/self-heal`  → open PR.

Watchdog Windows service
• Monitor Actions/AgentHub/Proxy/Ollama; restart with exponential backoff.
• Detect corrupt config; restore last known good; record diff.
• On update, run migrations; if health fails, auto-rollback.

Crash reporter
• Capture stack/log tail; write `logs/crash/*`; “Open logs” button in GUI.

CI
• Versioned migrations with tests.
• E2E: corrupt config + failed start → verify rollback & recovery.

Commits: `feat(self-heal): …`

──────────────────────────────────────────────────────────────────────────────
6) EPIC D — WORKFLOWS++ (smart & powerful)
──────────────────────────────────────────────────────────────────────────────
Branch: `feature/workflows-plus`  → open PR.

Add
• Workflow templates gallery (admin, git, media ops).
• “Suggest next workflow” based on terminal history + Logs/Jobs.
• Visual Pipeline editor: LLM → Tool → Script; save to YAML; run from GUI/CLI.
• Artifact viewer with open-in-folder.

Tests
• Parse/validate workflows; suggestion engine unit tests.
• E2E: create pipeline, run, view artifacts + logs.

Commits: `feat(workflows): …`

──────────────────────────────────────────────────────────────────────────────
7) EPIC E — INSTALLER POLISH (world-class one-click)
──────────────────────────────────────────────────────────────────────────────
Branch: `feature/installer-polish`  → open PR.

Installer
• Single EXE/MSI; admin detection + clear prompts; code-sign if keys provided.
• Preflight: disk, ports, firewall, VC runtimes, .NET if needed.
• Post-install: start services; auto-open First-Run wizard.
• Uninstall: option to keep models; clean logs; verify services removed.

Tests
• Scripted silent install/uninstall in CI (Windows runner).
• Verify services registered, firewall rules present, folders created.

Commits: `chore(installer): …`

──────────────────────────────────────────────────────────────────────────────
8) EPIC F — PERFORMANCE & QUALITY GATES
──────────────────────────────────────────────────────────────────────────────
Branch: `feature/perf-and-quality`  → open PR.

Add
• CI caches for npm/pip; parallel jobs; Windows self-hosted runner support.
• Perf tests for renderer boot (main window “ready”); budget TTI < 2.5s.
• `scripts/smoke.ps1`: /health checks, Proxy chat, workflow run; used post-install & in CI.
• README badge for CI status; `docs/first-run.md` quickstart.

Commits: `chore(ci): …`  
Update STATE and docs links.

──────────────────────────────────────────────────────────────────────────────
9) MAIN IMPLEMENTATION LOOP
──────────────────────────────────────────────────────────────────────────────
Process all tasks with `"status":"todo"` in `codex/STATE.json` in ascending order.
For each task:
  • Open its card in `codex/TASKS/` (or Appendix A title if not present).
  • Design → implement → unit+integration tests → run:
      npm test || true
      pytest   || true
      npm run build || true
  • Commit:
      git add -A
      git commit -m "feat(task-XX): <short description>"
  • Try push to main: `git push origin HEAD:main || PUSH_FAILED=1`
  • If main is protected or push fails:
      BR="codex/session-$(date +%Y%m%d-%H%M)-taskXX"
      git checkout -B "$BR"
      git push -u origin "$BR" || true
      if [ "${TOKEN}" != "YOUR_FINE_GRAINED_PAT" ]; then
        curl -s -X POST \
          -H "Authorization: token ${TOKEN}" \
          -H "Accept: application/vnd.github+json" \
          https://api.github.com/repos/Anthony5265/Windows-AI/pulls \
          -d "{\"title\":\"Codex: task XX\",\"head\":\"$BR\",\"base\":\"main\",\"body\":\"Automated by Codex. See codex/STATE.json.\"}" || true
      fi
      git checkout main || true
  • Update `codex/STATE.json` for this task:
      {"status":"done","commit":"<latest SHA or local-<timestamp>>","finished":"<ISO timestamp>"}
    Commit + push (best effort):
      git add codex/STATE.json
      git commit -m "chore(state): mark task XX done" || true
      git push origin HEAD:main || true

──────────────────────────────────────────────────────────────────────────────
10) SESSION CLOSEOUT
──────────────────────────────────────────────────────────────────────────────
──────────────────────────────────────────────────────────────────────────────
10) SESSION CLOSEOUT
──────────────────────────────────────────────────────────────────────────────
POST:
  TS="$(date +%Y-%m-%d_%H-%M)"
  mkdir -p codex/HISTORY
  {
    echo "# Codex Session ${TS}"
    echo
    echo "- Tasks completed: numbers + SHAs"
    echo "- Notable changes: bullets"
    echo "- CI status: summary"
    echo "- Follow-ups: bullets"
  } > codex/HISTORY/${TS}.md

  git add codex/HISTORY/${TS}.md
  git commit -m "docs(history): log Codex session ${TS}" || true
  git push origin HEAD:main || true
  git remote set-url origin https://github.com/Anthony5265/Windows-AI.git || true

──────────────────────────────────────────────────────────────────────────────
11) NO-REMOTE FALLBACK (ALWAYS AVAILABLE)
──────────────────────────────────────────────────────────────────────────────
If pushes/PRs are blocked, create a complete PATCH bundle for manual upload.

FALLBACK:
  mkdir -p PATCH_OUT
  git status --porcelain=v1 > PATCH_OUT/status.txt || true
  cp -r codex/STATE.json PATCH_OUT/ 2>/dev/null || true
  git diff --name-only > PATCH_OUT/filelist.txt || true
  while read f; do mkdir -p "PATCH_OUT/$(dirname "$f")"; cp -r "$f" "PATCH_OUT/$f" 2>/dev/null || true; done < PATCH_OUT/filelist.txt
  cat > PATCH_OUT/APPLY.md <<'EOF'
1) Download the ZIP and extract locally.
2) In GitHub → Add file → Upload files → drag-drop contents to the repo root.
3) Commit directly to main (or open a PR).
4) Run scripts/smoke.ps1 locally to verify.
EOF
  zip -r windowsai_patch.zip PATCH_OUT >/dev/null 2>&1 || true
  echo "-----BEGIN WINDOWS AI PATCH ZIP-----"
  base64 windowsai_patch.zip
  echo "-----END WINDOWS AI PATCH ZIP-----"

──────────────────────────────────────────────────────────────────────────────
12) APPENDIX A — 100-TASK BACKLOG (IMPLEMENT FULLY)
──────────────────────────────────────────────────────────────────────────────
# Titles only; implement with code + tests + docs until no TODO remains.
# 01 Repo scaffold & conventions
# 02 Windows installer baseline
# 03 Actions API service skeleton
# 04 Actions API normalized /api/actions/execute
# 05 AgentHub (FastAPI) skeleton + health
# 06 AgentHub → Actions adapter
# 07 LiteLLM Proxy wrapper
# 08 proxy.yaml + model mapping (local-first)
# 09 Model discovery & starter downloads
# 10 Electron GUI base app
# 11 GUI Chat MVP (streaming, model picker)
# 12 Logs/Jobs panel
# 13 Settings (ports, paths, TLS flag)
# 14 Terminal engine (xterm.js + node-pty)
# 15 Terminal themes/keysets loader
# 16 Workflow runner (shell/script/action)
# 17 AgentHub /workflows/run endpoint
# 18 Setup Agent (first-run wizard)
# 19 Self-healing watchdog
# 20 Auto-update & migrations
# 21 Security hardening (elevation/allowlists)
# 22 TLS (mkcert) integration
# 23 Local telemetry/metrics + UI sparkline
# 24 Smoke.ps1 + docs/first-run.md
# 25 Release pipeline & artifacts
# 26 Design system & accessibility
# 27 Chat tool-call inspector & transcript export
# 28 Model performance hints & cache
# 29 Visual pipeline editor
# 30 Workflow suggestions
# 31 Artifact viewer
# 32 Agent templates (ModularGen/CrewCore/CustomChain/MetaAgents)
# 33 Agent policy presets
# 34 Error UX & recovery flows
# 35 Config snapshots & restore points
# 36 External web tools default-off
# 37 Role-based quickstarts
# 38 Tray app & notifications
# 39 Windows service registration
# 40 Firewall rules
# 41 Hot model registry refresh
# 42 Chat file drop → tool inputs
# 43 Terminal session persistence
# 44 Unicode width + IME support
# 45 Global command palette
# 46 Global search (logs/workflows/settings)
# 47 Crash reporter & log bundler
# 48 Plugin SDK (local, safe)
# 49 Performance budget & measurement
# 50 Playwright visual regression tests
# 51 i18n scaffolding (EN seed)
# 52 Automated accessibility checks
# 53 Docs site polish
# 54 Quickstart media placeholders
# 55 Backup & restore (models/config)
# 56 Import/export workflows & themes as ZIP
# 57 Terminal keybinding editor UI
# 58 Workflow debugger (step-through)
# 59 Agent sandbox runner
# 60 API keys vault (Windows Credential Manager)
# 61 CLI companion
# 62 AgentHub tool registry
# 63 Pipeline ⇄ Workflow converter
# 64 Diagnostics report generator
# 65 High-contrast & large-text UX passes
# 66 Jobs scheduler (workflows)
# 67 Local artifact server (read-only, token)
# 68 Performance trace capture
# 69 Script sandbox policies
# 70 Privacy default-off
# 71 Error → docs mapping
# 72 Release notes generator (Conventional Commits)
# 73 DPI scaling fixes
# 74 Optional code signing
# 75 Portable (no-installer) build
# 76 Model offloading to external storage
# 77 Disk pressure alerts
# 78 Encrypted backups
# 79 Settings search
# 80 Explorer context menu integration
# 81 Agent evaluation harness
# 82 Multi-model voting/consensus
# 83 Model warmup & cache priming
# 84 Power profile integration
# 85 Battery & thermal guard (laptops)
# 86 Offline docs bundle
# 87 Scenario presets
# 88 Crash loop breaker
# 89 Release verification checklist
# 90 Local feedback export
# 91 About dialog (build, commit SHA)
# 92 License & third-party notices
# 93 Data directory relocation
# 94 Artifact/logs retention policy
# 95 Safe mode boot
# 96 Onboarding tour
# 97 App-wide search shortcut (Ctrl+/)
# 98 Error reproduction packs
# 99 Final QA end-to-end
# 100 GA release & docs

──────────────────────────────────────────────────────────────────────────────
13) ACCEPTANCE & STOP CONDITIONS
──────────────────────────────────────────────────────────────────────────────
• Six epics landed (merged or PRs open/green).
• 100-task backlog fully implemented.
• CI green.
• `codex/STATE.json` has no `"todo"`.
• Final `codex/HISTORY/<timestamp>.md` summary committed.
• If push/PR blocked: emit patch ZIP as in §11 and STOP.
