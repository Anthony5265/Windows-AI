# Windows AI - Comprehensive Testing Strategy

## Overview

This document outlines the complete testing strategy for Windows-AI to achieve and maintain 80%+ code coverage across all components.

## Testing Goals

- **80%+ Overall Code Coverage**: Combined Python and Node.js
- **90%+ Python Backend Coverage**: Core business logic
- **85%+ Node.js Services Coverage**: Actions API and common modules
- **75%+ GUI Coverage**: Electron application
- **Zero Flaky Tests**: All tests must be deterministic
- **Fast Execution**: < 10 minutes total CI time
- **Security Validation**: All OWASP Top 10 tested
- **Performance Baselines**: Regression detection

## Testing Stack

### Python Testing
- **pytest**: Test framework with async support
- **pytest-cov**: Coverage reporting
- **pytest-xdist**: Parallel execution
- **pytest-timeout**: Hanging test detection
- **pytest-mock**: Mocking utilities
- **pytest-benchmark**: Performance testing
- **httpx**: API testing
- **faker**: Test data generation

### Node.js Testing
- **Jest**: JavaScript/TypeScript testing
- **Supertest**: API endpoint testing
- **Playwright**: E2E GUI testing
- **Istanbul**: Coverage reporting

### Security Testing
- **safety**: Python dependency scanning
- **bandit**: Python security linting
- **semgrep**: Pattern-based security scanning
- **Custom**: OWASP Top 10 tests

### Performance Testing
- **locust**: Load testing
- **pytest-profiling**: Python profiling
- **memory-profiler**: Memory leak detection

## Test Organization

```
tests/
├── unit/                      # Unit tests (fast, isolated)
│   ├── backend/               # Python backend tests
│   │   ├── test_main_api.py   # FastAPI endpoint tests
│   │   ├── test_folder_watcher.py
│   │   ├── test_scheduler.py
│   │   └── test_plugin_registry.py
│   └── frontend/              # Node.js/GUI tests
├── integration/               # Integration tests
│   ├── backend_backend/       # Python to Python
│   ├── backend_actions/       # Python to Node.js
│   └── gui_backend/           # Electron to FastAPI
├── e2e/                       # End-to-end tests
│   ├── chat/                  # Chat interface workflows
│   ├── automation/            # Automation creation/execution
│   └── plugins/               # Plugin installation/usage
├── security/                  # Security tests
│   ├── injection/             # Injection attacks
│   ├── auth/                  # Authentication tests
│   └── owasp/                 # OWASP Top 10
├── performance/               # Performance tests
│   ├── benchmarks/            # Baseline benchmarks
│   └── load/                  # Load and stress tests
├── fixtures/                  # Shared test data
├── mocks/                     # External service mocks
└── helpers/                   # Test utilities
```

## Test Types

### 1. Unit Tests (`@pytest.mark.unit`)
- **Purpose**: Test individual functions/methods in isolation
- **Speed**: < 100ms per test
- **Coverage Goal**: 95%+
- **Isolation**: Mock all external dependencies
- **Example**: Test a single function with various inputs

### 2. Integration Tests (`@pytest.mark.integration`)
- **Purpose**: Test component interactions
- **Speed**: < 1 second per test
- **Coverage Goal**: 85%+
- **Dependencies**: May require database, filesystem
- **Example**: Test plugin registry loading and executing plugins

### 3. E2E Tests (`@pytest.mark.e2e`)
- **Purpose**: Test complete user workflows
- **Speed**: < 10 seconds per test
- **Coverage Goal**: Critical paths only
- **Environment**: Requires full application running
- **Example**: User creates automation and it executes successfully

### 4. Security Tests
- **Purpose**: Validate security posture
- **Speed**: Varies
- **Coverage**: OWASP Top 10
- **Tools**: bandit, safety, custom tests
- **Example**: Test SQL injection prevention

### 5. Performance Tests (`@pytest.mark.benchmark`)
- **Purpose**: Detect performance regressions
- **Speed**: 10-60 seconds per test
- **Baselines**: Stored in CI
- **Alert**: > 10% regression
- **Example**: Chat endpoint response time

## Coverage Targets by Module

### Python Backend (90%+)

| Module | Target | Priority |
|--------|--------|----------|
| windows_ai/main.py | 90% | Critical |
| windows_ai/folder_watcher.py | 95% | Critical |
| windows_ai/scheduler.py | 95% | Critical |
| windows_ai/plugins/registry.py | 85% | High |
| windows_ai/model_manager.py | 90% | High |
| windows_ai/updater/ | 85% | Medium |

### Node.js Services (85%+)

| Module | Target | Priority |
|--------|--------|----------|
| apps/actions-api/ | 90% | Critical |
| apps/gui/main.js | 75% | Medium |
| apps/gui/preload.js | 80% | Medium |
| apps/common/ | 90% | High |

### GUI (75%+)

| Component | Target | Priority |
|-----------|--------|----------|
| Chat Interface | 80% | Critical |
| Automation UI | 75% | High |
| Plugin Marketplace | 75% | High |
| Settings | 70% | Medium |

## Testing Best Practices

### 1. Test Independence
```python
# GOOD: Each test is independent
def test_create_user():
    user = create_user("test@example.com")
    assert user.email == "test@example.com"

def test_delete_user():
    user = create_user("test@example.com")
    delete_user(user.id)
    assert not user_exists(user.id)

# BAD: Tests depend on each other
def test_create_user():
    global user
    user = create_user("test@example.com")

def test_delete_user():
    delete_user(user.id)  # Depends on previous test
```

### 2. Arrange-Act-Assert Pattern
```python
def test_folder_watcher_detects_file():
    # Arrange: Setup test environment
    temp_dir = create_temp_directory()
    watcher = FolderWatcher(temp_dir)
    watcher.start()

    # Act: Perform the action
    create_file(temp_dir / "test.txt")

    # Assert: Verify the result
    assert watcher.events_detected == 1
    assert watcher.last_event.path == temp_dir / "test.txt"
```

### 3. Mock External Dependencies
```python
# GOOD: Mock external API
@patch('httpx.AsyncClient')
async def test_chat_endpoint(mock_client):
    mock_client.post.return_value = mock_response()
    result = await call_external_api()
    assert result["success"] is True

# BAD: Call real external API
async def test_chat_endpoint():
    result = await call_external_api()  # Flaky, slow
    assert result["success"] is True
```

### 4. Parameterized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
    (None, None)
])
def test_uppercase(input, expected):
    assert uppercase(input) == expected
```

### 5. Fixture Reuse
```python
@pytest.fixture
def temp_database():
    """Create temporary database for tests"""
    db = create_test_database()
    yield db
    db.cleanup()

def test_create_record(temp_database):
    record = temp_database.create({"name": "test"})
    assert record.name == "test"
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Types
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# E2E tests
pytest -m e2e

# Slow tests
pytest -m slow

# Security tests
pytest tests/security/
```

### Run with Coverage
```bash
# Generate coverage report
pytest --cov=windows_ai --cov-report=html

# View report
open htmlcov/index.html
```

### Run in Parallel
```bash
# Use 4 CPU cores
pytest -n 4
```

### Run Specific Module
```bash
pytest tests/unit/backend/test_main_api.py
```

### Run Specific Test
```bash
pytest tests/unit/backend/test_main_api.py::TestChatEndpoints::test_chat_endpoint_success
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: [3.11]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Quality Gates
- ✅ All tests must pass
- ✅ Coverage must be >= 80%
- ✅ No security vulnerabilities
- ✅ Performance within 10% of baseline

## Test Maintenance

### Adding New Tests
1. Create test file in appropriate directory
2. Follow naming convention: `test_[module]_[feature].py`
3. Use fixtures from `tests/fixtures/`
4. Add appropriate markers (`@pytest.mark.unit`, etc.)
5. Ensure test is deterministic
6. Run test locally before committing

### Fixing Flaky Tests
1. Identify flaky test (fails intermittently)
2. Add logging to understand failure
3. Check for timing issues (add proper waits)
4. Check for shared state (ensure isolation)
5. Mock external dependencies
6. Increase timeout if needed

### Updating Test Data
1. Update fixtures in `tests/fixtures/`
2. Ensure backward compatibility
3. Update dependent tests
4. Run full test suite

## Performance Baselines

### API Response Times
- Chat endpoint (first token): < 200ms
- List plugins: < 50ms
- System info: < 100ms
- Model list: < 150ms

### GUI Performance
- Application launch: < 3 seconds
- Tab switch: < 100ms
- Message render: < 50ms

### Automation Performance
- Folder watcher event detection: < 500ms
- Task execution accuracy: ± 5 seconds

## Security Testing

### OWASP Top 10 Coverage
1. ✅ Injection: SQL, Command, Path Traversal
2. ✅ Broken Authentication
3. ✅ Sensitive Data Exposure
4. ✅ XML External Entities
5. ✅ Broken Access Control
6. ✅ Security Misconfiguration
7. ✅ Cross-Site Scripting (XSS)
8. ✅ Insecure Deserialization
9. ✅ Components with Known Vulnerabilities
10. ✅ Insufficient Logging & Monitoring

### Security Test Examples
```python
# Test SQL Injection Prevention
def test_sql_injection():
    malicious_input = "' OR '1'='1"
    response = client.post("/chat", json={"message": malicious_input})
    assert response.status_code in [200, 400]
    assert "SQL" not in response.text

# Test Command Injection Prevention
def test_command_injection():
    malicious_command = "echo test; rm -rf /"
    response = client.post("/automation/tasks", json={
        "command": malicious_command
    })
    assert response.status_code in [400, 422]
```

## Continuous Improvement

### Weekly
- Review coverage reports
- Fix failing tests
- Update test data

### Monthly
- Review and update baselines
- Audit security tests
- Performance trend analysis

### Quarterly
- Major test refactoring
- Update testing dependencies
- Security audit

## Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **Playwright Docs**: https://playwright.dev/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/

## Support

For questions or issues with tests:
- Check this documentation
- Review existing tests for patterns
- Ask in team chat
- Create GitHub issue

---

**Last Updated**: 2024-11-10
**Version**: 1.0.0
