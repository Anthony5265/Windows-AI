# Contributing to Windows AI

Thank you for helping improve Windows AI! This guide covers everything you need to get started.

## Quick Start

1. **Fork & clone** the repository
2. **Install** dependencies: `pip install -e ".[dev]"` or `pip install -r requirements.txt && pip install -r requirements-test.txt`
3. **Run tests**: `python -m pytest tests/test_*.py -q --timeout=30`
4. **Make changes**, add tests, push, and open a PR

## Development Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/Windows-AI.git
cd Windows-AI

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Verify the setup
python -m pytest tests/test_quick_wins.py -v
```

## Code Style

- **Python 3.9+** — use type hints everywhere
- **Line length**: 120 characters max
- **Imports**: standard library → third-party → local, each group separated by a blank line
- **Docstrings**: Google style (`Args:`, `Returns:`, `Raises:`)
- **Error handling**: Always catch exceptions gracefully — the system must never crash from a plugin error

## Making Changes

### Adding a Plugin

1. Create a file in `windows_ai/plugins/builtin/<category>/`
2. Inherit from `Plugin` (from `windows_ai.plugins.base`)
3. Implement `async execute(self, **kwargs) -> Dict[str, Any]`
4. Add `plugin = YourPlugin()` at module level (required for discovery)
5. Write tests in `tests/`

### Adding an Integration Manager

1. Create a file in `windows_ai/integrations/`
2. Class takes no constructor arguments (`__init__(self)`)
3. Implement `async initialize(self)` (returns None, sets `self._initialized = True`)
4. Register in `windows_ai/integrations/__init__.py`
5. Write tests

### Adding an API Route

1. Create a route file in `windows_ai/api/`
2. Use FastAPI `APIRouter` with appropriate prefix and tags
3. Wire the router into `windows_ai/api/server.py`
4. Write tests

## Testing

```bash
# Run all tests
python -m pytest tests/test_*.py -q --timeout=30

# Run specific test file
python -m pytest tests/test_core_systems.py -v

# Run with coverage
python -m pytest tests/ --cov=windows_ai --cov-report=term-missing

# Run only unit tests (fast)
python -m pytest tests/ -m unit -q
```

### Test Conventions

- **File naming**: `tests/test_<module>.py`
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`, `@pytest.mark.critical`
- **Async tests**: use `@pytest.mark.asyncio` — the project uses `asyncio_mode = auto`
- **Mocking**: prefer `unittest.mock.patch` and `pytest-mock` over monkey-patching

## Pull Request Guidelines

- **Keep PRs focused** — one feature or fix per PR
- **Include tests** when altering runtime code
- **Update docs**: ROADMAP.md, CHANGELOG.md, and relevant docstrings
- **Commit messages**: follow [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `docs:`, `test:`, `chore:`
- **Branch naming**: `feat/<description>`, `fix/<description>`, `docs/<description>`

## Issue Reporting

- Use clear reproduction steps and expected vs. actual behavior
- Include Python version, OS, and relevant configuration
- Attach logs if available (check `~/.windows_ai/logs/`)

## Architecture Overview

See `BLUEPRINT.md` for the full architecture. Key principles:

- **Zero Configuration**: auto-detect everything; smart defaults
- **Graceful Degradation**: never crash — log errors and continue
- **Freedom First**: security features are OFF by default; users opt-in
- **Modular Design**: managers are independent and lazy-loaded

## Security

- Follow the "Freedom First" philosophy: restrictive features default to OFF
- Never commit secrets or API keys
- Use `windows_ai/security/` modules for crypto, RBAC, and sandboxing
- Report security vulnerabilities via GitHub Security Advisories (not public issues)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

