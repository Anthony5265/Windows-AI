# Windows AI
[![codecov](https://codecov.io/gh/Windows-AI/Windows-AI/branch/main/graph/badge.svg)](https://codecov.io/gh/Windows-AI/Windows-AI)

> **Transform any Windows PC into a cosmic, AI-first, automated OS ecosystem—instantly.**

Windows AI is a hyper-integrated overlay that turns ordinary devices into a
self-orchestrating intelligence mesh. It amplifies every pixel and process with
contextual automation, real-time reasoning, and cross-device awareness.

---

## 🧬 Key Features & One-Click Actions

### **🌐 Universal AI OS Overlay**
- **AI-augmented File Explorer** – Summarize, search, organize, batch-rename, or move files with natural language.
- **AI Terminal (Custom Shell)** – Generate code, run commands, automate scripts
  with GPT-powered suggestions.
- **AI Task Manager** – Analyze and optimize resource usage; terminate, restart, or schedule apps with AI insight.
- **AI Settings/Control Panel** – Let AI tune power, performance, accessibility, privacy, and UI themes for you.
- **AI Start Menu & Launcher** – Voice-search, summarize, or batch-launch apps and workflows.
- **AI Notification Center** – Summarized, actionable notifications; “Remind me,” “Schedule meeting,” or “Take note.”

## **🧠 AI Mesh and Automation**
- **One-click Mesh Expansion** – Instantly add new PCs, laptops, VMs, and smart devices to your Windows AI network.
- **Device Handoff** – Move tasks/agents between devices: “Continue on my laptop.”
- **Distributed LLM Inference** – Pool compute; run local LLMs on your beefiest hardware automatically.
- **Family/Team Dashboard** – Unified device and AI workflow management for everyone at home or work.

---

## Development Setup

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
npm install  # installs dependencies and sets up Husky git hooks
```

Run `pytest` and `npm test` to verify changes before submitting pull requests.

## GPT-based Workflows

All AI-assisted jobs use the `gpt-4.1-nano` model. A single workflow, [`gpt-review.yml`](.github/workflows/gpt-review.yml), runs GPT-powered checks through a reusable [composite action](.github/actions/gpt-request/action.yml):

- **code-review** – runs the ChatGPT Code Review action on pull requests.
- **commit-message-review** – ensures the latest commit message is clear and actionable.
- **commit-summary** – produces a short summary of the most recent changes.

Set the `OPENAI_API_KEY` secret to enable these jobs.

## GitHub Actions Secrets

The GPT-powered workflows require an OpenAI API key.

1. In your repository on GitHub, navigate to **Settings > Secrets and variables > Actions**.
2. Choose **New repository secret** and name it `OPENAI_API_KEY`.
3. Paste your OpenAI API key and save.

A lightweight workflow, [`openai-key-check.yml`](.github/workflows/openai-key-check.yml), verifies the secret by calling `gpt-4.1-nano`. Run it from the **Actions** tab to confirm the key is configured correctly.
