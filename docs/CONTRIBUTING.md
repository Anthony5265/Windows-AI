# Contributing to Windows AI

Thank you for your interest in contributing to Windows AI!

## Current Development Status

Windows AI is in **active development (alpha)**. We are:
- Building out comprehensive testing
- Improving documentation
- Expanding the plugin ecosystem
- Preparing for beta release

## How to Contribute

### 1. Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/Anthony5265/Windows-AI.git
cd Windows-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-test.txt

# Run tests
pytest tests/
```

### 2. Areas That Need Help

#### High Priority
- **Testing:** Increase test coverage from current to 60%+
- **Documentation:** Document individual plugins
- **Plugin Testing:** Verify plugins work with real APIs
- **Security:** Security audit and fixes

#### Medium Priority
- **Agent System:** Complete agent orchestration
- **Performance:** Optimize plugin loading
- **Examples:** Create usage examples
- **Tutorials:** Write getting-started guides

#### Low Priority
- **Mobile Apps:** Build iOS/Android apps
- **IoT:** Implement IoT integrations
- **XR:** Add VR/AR support

### 3. Plugin Development

See our [Plugin Development Guide](docs/development/PLUGIN_DEVELOPMENT.md)
for how to create new plugins.

**Plugin Quality Standards:**
- Real API implementation (not template/placeholder)
- Async/await patterns
- Full error handling
- Type hints throughout
- Tests with 60%+ coverage
- Documentation with examples

### 4. Code Quality Standards

All contributions must:
- ✅ Pass all tests (`pytest tests/`)
- ✅ Pass linting (`ruff check .`)
- ✅ Have type hints (`mypy windows_ai/`)
- ✅ Include tests (60%+ coverage for new code)
- ✅ Update documentation

### 5. Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

#### Pull Request Guidelines

- Clear description of changes
- Reference any related issues
- Include test results
- Update CHANGELOG.md

### 6. Code Review Process

All PRs are reviewed for:
- Code quality
- Test coverage
- Documentation
- Security implications
- Performance impact

### 7. Community

- **Issues:** Report bugs and request features on GitHub
- **Discussions:** Ask questions in GitHub Discussions
- **Security:** Report security issues via email (see SECURITY.md)

## License

By contributing, you agree that your contributions will be licensed
under the MIT License.

---

Thank you for helping make Windows AI better!
