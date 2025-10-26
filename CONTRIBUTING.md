# Contributing

Thanks for your interest in improving Windows AI!

## Pull Requests

- Keep your branch up to date with `main`. The `main` branch is protected and requires pull requests to be up to date before merging.
- Pull requests are merged via the **merge queue**. Add the `ready-to-merge` label to enqueue your PR and let Mergify handle the merge once checks pass.
- **Do not use the "Merge" button.** Every PR must be enqueued; manual merges to `main` are prohibited.

Please ensure tests pass locally before requesting a review.

## Branching and rebasing

- Create feature branches from `main`.
- Before pushing, run `git fetch origin && git rebase origin/main`.
- Resolve conflicts locally before opening or refreshing a PR.

## Commit Messages

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.
Each commit message should be structured as:

```
<type>(optional scope): <description>
```

Examples:

- `feat: add OAuth support`
- `fix(ui): correct button color`
- `chore: update dependencies`

Commit messages are linted with Commitlint via a pre-commit `commit-msg` hook.

## Releases

- Label pull requests so Release Drafter can categorize them (e.g. `feature`, `enhancement`, `bug`, `documentation`, `docs`, `chore`, `refactor`).
- Draft releases are updated automatically by Release Drafter whenever changes are merged to `main`.
- To publish a new release:
  1. Open the draft release on GitHub.
  2. Review the generated notes and version, adjusting as needed.
  3. Publish the release to create the tag.

