# Contributing

Thanks for your interest in improving Windows AI!

## Pull Requests

- Keep your branch up to date with `main`. The `main` branch is protected and requires pull requests to be up to date before merging.
- Pull requests are merged via the **merge queue**. Add the `ready-to-merge` label to enqueue your PR and let Mergify handle the merge once checks pass.
- **Do not merge manually.** All changes must go through the queue.

Please ensure tests pass locally before requesting a review.

## Pre-commit

We use [pre-commit](https://pre-commit.com/) to manage formatting and linting. Install and run the hooks before committing:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
