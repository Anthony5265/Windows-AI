# VS Code Configuration Setup Complete

## Overview
Created comprehensive VS Code configuration for Windows-AI development with one-click workflows.

## Files Configured

### 1. `.vscode/settings.json` (Updated)
- **Python environment**: Auto-detect venv interpreter
- **Linting**: Flake8 (120 char line length)
- **Formatting**: Black (auto-format on save)
- **Testing**: pytest with auto-discovery
- **Editor**: Format on save, organize imports, 120-char ruler
- **File exclusions**: Hide `__pycache__`, `.pytest_cache`, `venv`, etc.
- **Auto-save**: 1-second delay

### 2. `.vscode/launch.json` (Created)
Debug configurations for all major components:

| Configuration | Purpose | Port/Args |
|--------------|---------|-----------|
| **Python: Backend Server** | Run FastAPI backend with hot reload | uvicorn :8000 |
| **Python: GUI Control Center** | Launch main GUI | gui.py |
| **Python: Mesh GUI** | Launch mesh GUI | mesh_gui.py |
| **Python: Current File** | Debug active file | - |
| **Python: Debug Tests** | Debug current test file | pytest -v |
| **Python: Debug Specific Test** | Debug single test function | Prompts for name |
| **Python: Security Tests** | Run security tests only | pytest tests/security/ -m critical |
| **Python: All Tests** | Run full test suite | pytest tests/ |
| **Python: Tests with Coverage** | Run tests + coverage report | pytest --cov |
| **Python: Plugin System** | Debug plugin manager | plugin_manager.py |
| **Python: Agent Orchestrator** | Debug agent orchestrator | orchestrator.py |

All configurations set `PYTHONPATH` and use `integratedTerminal`.

### 3. `.vscode/tasks.json` (Created)
One-click tasks for common operations:

#### Build/Run Tasks
- **Run Backend Server** (background): Uvicorn with hot reload on :8000
- **Run GUI Control Center**: Launch main GUI
- **Run Mesh GUI**: Launch mesh GUI

#### Test Tasks
- **Run All Tests** (default test task): Full pytest suite
- **Run Security Tests**: Security-only suite
- **Run Tests with Coverage**: Generate HTML coverage report
- **Run Current Test File**: Test active file

#### Code Quality Tasks
- **Format Code (Black)**: Auto-format entire codebase
- **Lint Code (Flake8)**: Check code style (with problem matcher)
- **Type Check (mypy)**: Static type checking (with problem matcher)

#### Maintenance Tasks
- **Install Dependencies**: Install production requirements
- **Install Dev Dependencies**: Install dev requirements
- **Build Installer**: Run build.py
- **Clean Build Artifacts**: Remove dist/, build/, caches, etc.

### 4. `.vscode/extensions.json` (Existing)
Recommended extensions already configured.

## One-Click Workflows Enabled

### 1️⃣ Start Backend Server
- **Method 1**: Press `F5` → Select "Python: Backend Server"
- **Method 2**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Backend Server"
- **Result**: Backend runs on http://127.0.0.1:8000 with hot reload

### 2️⃣ Launch GUI
- **Method 1**: Press `F5` → Select "Python: GUI Control Center"
- **Method 2**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run GUI Control Center"
- **Result**: GUI launches and connects to backend

### 3️⃣ Run Tests
- **Method 1**: Press `Ctrl+Shift+T` (default test task)
- **Method 2**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run All Tests"
- **Method 3**: Right-click test file → "Run Python Tests"
- **Result**: Full test suite executes with verbose output

### 4️⃣ Run Security Tests
- **Press `F5`** → Select "Python: Security Tests"
- **Result**: 41 security tests execute (critical marker)

### 5️⃣ Debug Current File
- **Open any Python file** → Press `F5` → Select "Python: Current File"
- **Result**: Debugger attaches to current file

### 6️⃣ Format & Lint Code
- **Format**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Format Code (Black)"
- **Lint**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Lint Code (Flake8)"
- **Auto-format**: Save any Python file (automatic)

## Testing Workflows

### Debug Failing Test
1. Open test file (e.g., `tests/security/test_critical_security.py`)
2. Press `F5` → Select "Python: Debug Tests"
3. Debugger stops at breakpoints in test
4. Step through test execution

### Debug Specific Test Function
1. Press `F5` → Select "Python: Debug Specific Test"
2. Enter test name (e.g., `test_plugin_sandbox`)
3. Debugger runs only that test

### Run Tests with Coverage
1. `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Tests with Coverage"
2. Coverage report generated in `htmlcov/index.html`
3. Open report: `htmlcov/index.html` in browser
4. Coverage gutters show line coverage in editor

## Development Workflow

### Standard Development Cycle
```
1. Start backend: Ctrl+Shift+P → "Run Backend Server"
2. Launch GUI: Ctrl+Shift+P → "Run GUI Control Center"
3. Make code changes (auto-save after 1 second)
4. Code auto-formats on save
5. Run tests: Ctrl+Shift+T
6. Debug if needed: F5 → "Debug Tests"
```

### Pre-Commit Workflow
```
1. Format code: Ctrl+Shift+P → "Format Code (Black)"
2. Lint code: Ctrl+Shift+P → "Lint Code (Flake8)"
3. Type check: Ctrl+Shift+P → "Type Check (mypy)"
4. Run security tests: F5 → "Security Tests"
5. Run all tests: Ctrl+Shift+T
6. Check coverage: "Run Tests with Coverage"
```

## Configuration Benefits

### 🎯 One-Click Operations
- No terminal commands needed
- All common tasks accessible via UI
- Keyboard shortcuts for frequent operations

### 🔍 Integrated Debugging
- 11 debug configurations covering all components
- Breakpoints work across backend, GUI, tests
- Step-through debugging for all Python code

### ✅ Automated Quality Checks
- Auto-format on save (Black)
- Auto-organize imports
- Problem matchers for Flake8, mypy
- Errors appear in Problems panel

### 🧪 Testing Integration
- Discover tests automatically
- Run tests via UI or shortcuts
- Debug tests with breakpoints
- Coverage visualization in editor

### ⚡ Hot Reload
- Backend auto-reloads on code changes
- No need to restart server during development
- Instant feedback on API changes

## File Structure
```
.vscode/
├── settings.json    ✅ Updated (Python dev settings added)
├── launch.json      ✅ Created (11 debug configurations)
├── tasks.json       ✅ Created (14 tasks)
└── extensions.json  ✅ Existing (recommended extensions)
```

## Verification Steps

### Test Backend Server Task
```powershell
# Should start uvicorn on :8000
Ctrl+Shift+P → "Tasks: Run Task" → "Run Backend Server"
# Navigate to http://127.0.0.1:8000/docs
```

### Test GUI Launch
```powershell
# Should open GUI window
Ctrl+Shift+P → "Tasks: Run Task" → "Run GUI Control Center"
```

### Test Test Suite
```powershell
# Should run pytest with verbose output
Ctrl+Shift+T
```

### Test Debug Configuration
```powershell
# Should attach debugger to backend
F5 → Select "Python: Backend Server"
# Set breakpoint in windows_ai/api/server.py
# Make API request to trigger breakpoint
```

## Success Criteria Met

✅ **One-click backend**: Run Backend Server task starts uvicorn  
✅ **One-click GUI**: Run GUI Control Center task launches GUI  
✅ **One-click tests**: Ctrl+Shift+T runs full test suite  
✅ **Debug configurations**: 11 configs covering all components  
✅ **Code quality**: Auto-format, auto-lint, problem matchers  
✅ **Hot reload**: Backend task configured with --reload  
✅ **Test discovery**: pytest auto-discovers tests on save  
✅ **Coverage**: Task generates HTML coverage report  

## Integration with Master Plan

This configuration fulfills **Section 8.1** of the master plan:
> "One-click: run backend, run GUI, run tests"

Developers can now:
- Start backend with 1 keyboard shortcut
- Launch GUI with 1 keyboard shortcut  
- Run tests with 1 keyboard shortcut
- Debug any component with breakpoints
- Auto-format code on every save
- See linting errors in real-time

## Next Steps (Section 8.2)

1. Create `.github/workflows/ci.yml` (CI/CD pipeline)
2. Configure 4-stage pipeline (unit → integration → security → e2e)
3. Enforce 60%+ coverage threshold
4. Set up security tests as merge blocker
5. Add automated code quality checks

## Related Documentation

- Master Plan: `docs/roadmaps/MASTER_ROADMAP_CONSOLIDATED.md`
- Security Tests: `tests/security/README.md`
- Test Results: `docs/master_plan/SECURITY_TEST_RESULTS.md`
- Configuration System: `docs/CONFIGURATION_MIGRATION.md`

---

**Status**: ✅ VS Code configuration complete (Task 15/17)  
**Next**: Implement CI/CD pipeline (Task 16/17)  
**Progress**: 88% of Phase 1 complete
