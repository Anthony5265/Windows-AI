# Contributing

Thanks for your interest in improving Windows AI!

## Pull Requests

- Keep your branch up to date with `main`. The `main` branch is protected and requires pull requests to be up to date before merging.
- Pull requests are merged via the **merge queue**. Add the `ready-to-merge` label to enqueue your PR and let Mergify handle the merge once checks pass.
- **Do not merge manually.** All changes must go through the queue.

Please ensure tests pass locally before requesting a review.

## Pre-commit

- Create feature branches from `main`.
- Before pushing, run `git fetch origin && git rebase origin/main`.
- Resolve conflicts locally before opening or refreshing a PR.

## Development Container

This repository includes a VS Code Dev Container configuration to provide a
consistent development environment.

1. Install [Visual Studio Code](https://code.visualstudio.com/) and the **Dev Containers** extension.
2. Open the command palette and run **Dev Containers: Open Folder in Container...** (or **Reopen in Container** if the folder is already open).
3. Select the repository folder and VS Code will build the container using the provided `Dockerfile`.
4. After the build completes, all project build and test dependencies are available inside the container.

## Releases

- Draft releases are updated automatically whenever changes are merged to `main`.
- To publish a new release:
  1. Open the draft release on GitHub.
  2. Review and adjust the notes and version as needed.
  3. Publish the release to create the tag.

