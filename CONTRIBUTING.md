# Contributing

Thanks for your interest in improving Windows AI!

## Repository Organization

Before contributing, please familiarize yourself with our repository structure:

- **Start with the [Repository Map](docs/structure/overview.md)** for a curated view of every top-level folder and file
- **Read [docs/DIRECTORY_STRUCTURE.md](docs/DIRECTORY_STRUCTURE.md)** for a comprehensive guide to all directories
- **Follow organization principles** outlined in the directory structure guide
- **Keep the root directory clean** - only essential documentation and launch scripts belong there
- **Place code in appropriate directories**:
  - Python backend code → `windows_ai/`
  - Node.js services → `apps/` or appropriate named directory
  - Tests → `tests/` (mirror source structure)
  - Documentation → `docs/`
  - Plugins → `plugins/[category]/`
  - Scripts → `scripts/`

### File Placement Guidelines

| What You're Adding | Where It Goes |
|--------------------|---------------|
| Python backend code | `windows_ai/` |
| Node.js service | `apps/` or new named directory |
| Plugin | `plugins/[category]/` |
| Test | `tests/` (mirror source structure) |
| User documentation | `docs/` |
| API documentation | `docs/reference/api/overview.md` or `openapi/` |
| Build/utility script | `scripts/` (or root if essential) |
| Repo catalog updates | `docs/structure/` (update YAML + regenerate manifest) |

## Pull Requests

- Keep your branch up to date with `main`. The `main` branch is protected and requires pull requests to be up to date before merging.
- Pull requests are merged via the **merge queue**. Add the `ready-to-merge` label to enqueue your PR and let Mergify handle the merge once checks pass.
- **Do not use the "Merge" button.** Every PR must be enqueued; manual merges to `main` are prohibited.

Please ensure tests pass locally before requesting a review.

## Branching and rebasing

This project uses [pre-commit](https://pre-commit.com/) to run linters and formatters.

- Install pre-commit with `pip install pre-commit`.
- Run `pre-commit install` to set up the git hook.
- Before pushing, run `pre-commit run --all-files`.
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

## Code Organization Best Practices

### Don't Commit These Files
- Temporary files (`tmp*.txt`, `*.tmp`)
- Build artifacts (except reference releases)
- Session logs (`*SESSION*.md`, `*WORK_SESSION*.md`)
- Large binary files (document download locations instead)
- Test data files (unless essential for tests)

These are already in `.gitignore`, but be mindful when using `git add .`

### Keep Things Organized
- Remove temporary files before committing
- Update documentation when changing structure
- Add tests in the appropriate `tests/` subdirectory
- Follow existing naming conventions
- Use descriptive directory and file names

## Releases

- Label pull requests so Release Drafter can categorize them (e.g. `feature`, `enhancement`, `bug`, `documentation`, `docs`, `chore`, `refactor`).
- Draft releases are updated automatically by Release Drafter whenever changes are merged to `main`.
- To publish a new release:
  1. Open the draft release on GitHub.
  2. Review the generated notes and version, adjusting as needed.
  3. Publish the release to create the tag.
