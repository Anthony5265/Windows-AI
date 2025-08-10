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

## Stale Issues and Pull Requests

Issues and pull requests with no activity for 30 days are automatically
labeled `stale` and will be closed after another 30 days without activity.
Any comment or code change removes the `stale` label and resets the timer.
Keep the conversation going or add updates to avoid automatic closing.
