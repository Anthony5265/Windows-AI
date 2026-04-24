# Provider Setup Preflight

Windows AI uses provider setup preflight data during installation and first-run setup to decide which AI CLIs and local runtimes are ready, which need authentication, and which need installation.

## Scripts

- `detect-ai-providers.ps1` scans the machine and writes a provider setup JSON file.
- `validate-provider-setup.ps1` validates that setup JSON has the expected shape.
- `run-provider-preflight.ps1` runs detection and validation as one installer-friendly command.

## Basic usage

```powershell
./install/run-provider-preflight.ps1
```

By default, the runner writes to:

```text
$env:TEMP\windows-ai-provider-setup.json
```

To write somewhere else:

```powershell
./install/run-provider-preflight.ps1 -OutputPath C:\Temp\windows-ai-provider-setup.json
```

To skip validation during local debugging:

```powershell
./install/run-provider-preflight.ps1 -SkipValidation
```

## Output contract

The setup JSON includes:

- `providers` — raw detection results for Gemini CLI, Codex CLI, Claude CLI, Grok CLI, and Ollama.
- `hardware` — lightweight Windows hardware profile.
- `ollama` — recommended local models, `default_model_id`, and `default_target`.
- `target_catalog` — normalized chat targets split into ready and setup-required groups.
- `installer_actions` — simple per-provider action hints for the installer.

`target_catalog` is the preferred installer and GUI model-picker input because it already contains direct chat targets such as `cli:codex` and `ollama:phi3:mini`.

## Validation

The validator checks that:

- required top-level objects exist,
- provider actions are one of `ready`, `authenticate`, or `install`,
- Ollama does not require cloud authentication,
- Ollama model recommendations include direct `ollama:<model>` targets,
- target catalog entries include provider ids, target strings, and valid action states.

The JSON schema is stored at:

```text
install/provider-setup.schema.json
```
