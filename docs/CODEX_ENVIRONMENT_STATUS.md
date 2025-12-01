# Codex Environment Status

The automated environment scorecard reports that all required tooling is
installed except for the local Python virtual environment expected at
`.venv/`. To bring the Codex workspace on ChatGPT fully in line with the
recommended setup, create the virtual environment by running:

```bash
python scripts/dev/bootstrap_env.py
```

This command provisions the `.venv` directory and installs the repository's
Python and Node.js dependencies.
