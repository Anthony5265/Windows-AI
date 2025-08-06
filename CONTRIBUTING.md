# Contributing

Thanks for your interest in improving Windows AI!

## Pull Requests

- Keep your branch up to date with `main`. The `main` branch is protected and requires pull requests to be up to date before merging.
- Pull requests are merged via the **merge queue**. Add the `ready-to-merge` label to enqueue your PR and let Mergify handle the merge once checks pass.
- **Do not merge manually.** All changes must go through the queue.

Please ensure tests pass locally before requesting a review.

## Branching and Rebasing

- Create feature branches from `main`.
- Before pushing, run `git fetch origin && git rebase origin/main`.
- Resolve conflicts locally before opening or refreshing a PR.

## Development Container

This repository includes a preconfigured development container for VS Code.

1. Install Docker, VS Code, and the Dev Containers extension.
2. Open the command palette and run **Dev Containers: Reopen in Container**.
3. VS Code will build the container using the provided `Dockerfile` and open the workspace inside.

The container includes all Python and Node.js dependencies so you can run `pytest` and `npm test` directly inside the environment.

## Local Setup

If you prefer to work outside the development container:

1. Create and activate a Python virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

2. Install Node.js dependencies and set up Git hooks:

   ```bash
   npm install
   ```

   The `prepare` script runs `husky install` to configure commit hooks.

Run `npm test` and `pytest` before opening a pull request to ensure everything passes.
