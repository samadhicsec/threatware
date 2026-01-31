# Integration Testing Plan for Threatware

## Overview

This document outlines an integration testing strategy for threatware that focuses on Phase 1 (Foundation) and Phase 2 (Management Features) to verify that the main CLI actions (convert, verify, manage.create, manage.indexdata, manage.submit) can be invoked without compilation errors, missing libraries, or bad import statements.

**Scope**: Smoke tests to ensure actions are callable and dependencies are properly installed.

## Testing Framework

- **Framework**: pytest (installed in dedicated `.venv-test` virtual environment)
- **Testing Type**: Integration tests using subprocess calls to CLI
- **Test Approach**: CLI-based smoke tests validating invocation and basic output
- **Virtual Environment**: `.venv-test` (separate from main threatware environment)
- **Additional Tools**: 
  - `subprocess` module for CLI invocation
  - `tempfile` module for isolated test environments
  - `git` command-line tool for git repo management
  - pytest fixtures for test setup/teardown

## Manual Setup Requirements

Before running the integration test suite, the following one-time setup is required:

### 1. Create Dedicated Test Virtual Environment

```bash
cd <path-to-threatware-repo>

# Create the test virtual environment
python3 -m venv .venv-test

# Activate it
source .venv-test/bin/activate

# Install test dependencies
pip install pytest pytest-cov

# Deactivate when done
deactivate
```

This keeps test-specific dependencies (pytest, etc.) separate from the main threatware installation.

**Note**: Steps 2-5 below are automated by pytest fixtures and run before each test suite execution.

## Test Structure

```
test/
├── integration/
│   ├── __init__.py
│   ├── conftest.py                           # Fixtures and setup
│   ├── test_data/
│   │   └── threat_models/                    # Local git repo for testing manage actions
│   ├── test_cli_convert.py                   # Test convert action with Google Doc
│   ├── test_cli_verify.py                    # Test verify action with Google Doc
│   └── test_cli_manage.py                    # Test manage.* actions with git integration
```

## Test Categories

### 1. **Convert Action Tests** (`test_cli_convert.py`)

Tests that the convert CLI action can be invoked without import or dependency errors using the real Google Doc.

**Google Doc ID**: `11IKk9cqj7ybfc6aJ6rlBDLC9_l4yE9L094C0m1YDt4g`

**Scenarios to test:**

- CLI help/version works (no import errors)
- convert action is available (--help works)
- convert can be invoked with the real Google Doc without crashing on imports
- convert can be invoked with the googledoc_1.0 scheme without import errors
- Basic error handling (no segfaults or unhandled exceptions on import failures)

**Example test cases:**

```python
def test_convert_action_available()
def test_convert_help_runs_without_errors()
def test_convert_google_doc_produces_valid_json()
def test_convert_cli_command_exists()
```

### 2. **Verify Action Tests** (`test_cli_verify.py`)

Tests that the verify CLI action can be invoked without import or dependency errors using the real Google Docs.

**Google Doc ID**: `11IKk9cqj7ybfc6aJ6rlBDLC9_l4yE9L094C0m1YDt4g`
**Template Doc ID**: `1DBskRZBKpolIchljkVowFsvB-xRlSVf8sPguOnxsnhU`

**Scenarios to test:**

- CLI help works (no import errors)
- verify action is available (--help works)
- verify can be invoked with the real Google Doc and template without crashing on imports
- verify can be invoked with the googledoc_1.0 scheme without import errors
- No library/import errors occur
- Produces valid JSON output with result field

**Example test cases:**

```python
def test_verify_action_available()
def test_verify_help_runs_without_errors()
def test_verify_google_doc_produces_valid_json()
```

### 3. **Manage Action Tests** (`test_cli_manage.py`)

Tests that the manage CLI actions can be invoked without import or dependency errors.

**Scenarios to test:**

- CLI help works (no import errors)
- manage.create action is available
- manage.indexdata action is available
- manage.submit action is available
- Each can be invoked without crashing on imports
- Git operations don't fail due to import errors

**Example test cases:**

```python
def test_manage_create_help_runs_without_errors()
def test_manage_indexdata_help_runs_without_errors()
def test_manage_submit_help_runs_without_errors()
def test_manage_cli_command_exists()
def test_manage_actions_workflow()
```

## Test Data Strategy

### Automated Test Data Setup

Before each test run, pytest automatically:

1. **Clones threatware-config repository** from https://github.com/samadhicsec/threatware-config.git
2. **Copies authentication token** from `~/.threatware/token.json` to the cloned repo
3. **Sets THREATWARE_CONFIG_DIR environment variable** to point to the cloned repo
4. **Creates a local git repository** for threat model storage
5. **Updates manage_config.yaml** with the path to the local git repository

After all tests complete, the `test_data` directory is automatically cleaned up.

**Directory Structure (Created Automatically)**:

```
test/integration/test_data/                  # Created before tests, removed after
├── threatware-config/                       # Cloned from GitHub
│   ├── manage/
│   │   └── manage_config.yaml               # Updated with local git repo path
│   ├── token.json                           # Copied from ~/.threatware/token.json
│   └── [other config files]
└── threat_models/                           # Local git repo for manage tests
    └── [empty git repo with initial commit]
```

**Key Configuration Points:**

- The `threatware-config` directory is a fresh clone of the official repository
- The `manage/manage_config.yaml` file is updated with the path to the local test git repository
- The `token.json` authentication file is copied from the user's home directory
- The environment variable `THREATWARE_CONFIG_DIR` is set during the test session
- All test data is cleaned up after tests complete, leaving no artifacts

### Real Google Doc

Tests will use a real Google Doc instead of local files:

- **Document ID**: `11IKk9cqj7ybfc6aJ6rlBDLC9_l4yE9L094C0m1YDt4g`
- **Scheme**: `googledoc_1.0` (standard threatware Google Docs format)
- **Purpose**: Validate that CLI can interact with Google Docs API without import errors
- **Accessibility**: Must be publicly accessible or accessible to authenticated user
- **Authentication**: Uses token from `~/.threatware/token.json`

## Pytest Configuration

Create `test/integration/conftest.py` with fixtures that automatically set up and clean up test data:

```python
import pytest
import subprocess
import shutil
import tempfile
import os
import yaml
from pathlib import Path

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "test_data"
THREATWARE_CONFIG_CLONE_DIR = TEST_DATA_DIR / "threatware-config"
THREAT_MODELS_REPO_DIR = TEST_DATA_DIR / "threat_models"

@pytest.fixture(scope="session", autouse=True)
def setup_and_cleanup_test_data():
    """
    Automatically set up test data before all tests and clean up after.
    This runs once per test session.
    """
    # Create test_data directory
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Clone threatware-config repository
    print(f"\n[Setup] Cloning threatware-config to {THREATWARE_CONFIG_CLONE_DIR}")
    if THREATWARE_CONFIG_CLONE_DIR.exists():
        shutil.rmtree(THREATWARE_CONFIG_CLONE_DIR)
    subprocess.run(
        ["git", "clone", "https://github.com/samadhicsec/threatware-config.git", 
         str(THREATWARE_CONFIG_CLONE_DIR)],
        check=True,
        capture_output=True
    )
    
    # Step 2: Copy authentication token
    token_src = Path.home() / ".threatware" / "token.json"
    token_dst = THREATWARE_CONFIG_CLONE_DIR / "token.json"
    if token_src.exists():
        print(f"[Setup] Copying token.json to cloned repo")
        shutil.copy2(token_src, token_dst)
    else:
        print(f"[Setup] Warning: token.json not found at {token_src}")
    
    # Step 3: Create local git repository for threat models
    print(f"[Setup] Creating local threat models git repository at {THREAT_MODELS_REPO_DIR}")
    if THREAT_MODELS_REPO_DIR.exists():
        shutil.rmtree(THREAT_MODELS_REPO_DIR)
    THREAT_MODELS_REPO_DIR.mkdir(parents=True, exist_ok=True)
    
    subprocess.run(
        ["git", "init", "--initial-branch", "approved"],
        cwd=THREAT_MODELS_REPO_DIR,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "--allow-empty-message", "-m", ""],
        cwd=THREAT_MODELS_REPO_DIR,
        check=True,
        capture_output=True,
        env={**os.environ, "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@test.com"}
    )
    
    # Step 4: Update manage_config.yaml with local git repository path
    manage_config_file = THREATWARE_CONFIG_CLONE_DIR / "manage" / "manage_config.yaml"
    if manage_config_file.exists():
        print(f"[Setup] Updating manage_config.yaml with local git repo path")
        with open(manage_config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update the remote path to point to local git repo
        if 'manage-config' not in config:
            config['manage-config'] = {}
        if 'storage' not in config['manage-config']:
            config['manage-config']['storage'] = {}
        if 'gitrepo' not in config['manage-config']['storage']:
            config['manage-config']['storage']['gitrepo'] = {}
        
        config['manage-config']['storage']['gitrepo']['remote'] = f"file://{THREAT_MODELS_REPO_DIR}"
        
        with open(manage_config_file, 'w') as f:
            yaml.dump(config, f)
        
        print(f"[Setup] Updated remote to: file://{THREAT_MODELS_REPO_DIR}")
    else:
        print(f"[Setup] Warning: manage_config.yaml not found at {manage_config_file}")
    
    # Set environment variable
    os.environ["THREATWARE_CONFIG_DIR"] = str(THREATWARE_CONFIG_CLONE_DIR)
    print(f"[Setup] Set THREATWARE_CONFIG_DIR={THREATWARE_CONFIG_CLONE_DIR}")
    
    # Yield control to run tests
    yield
    
    # Cleanup after all tests
    print(f"\n[Cleanup] Removing test_data directory")
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)
    print(f"[Cleanup] Test data cleanup complete")

@pytest.fixture
def threatware_cli():
    """Return the threatware CLI command that runs the source code directly."""
    return ["python3", "-m", "threatware.actions.handler"]

@pytest.fixture
def threatware_config_dir():
    """Return the threatware config directory path for manage tests"""
    return str(THREATWARE_CONFIG_CLONE_DIR)

@pytest.fixture
def threat_models_repo():
    """Return the local threat models git repository path"""
    return str(THREAT_MODELS_REPO_DIR)

@pytest.fixture
def isolated_git_repo(tmp_path):
    """Create isolated git repo for manage command tests"""
    repo_path = tmp_path / "threatmodels"
    repo_path.mkdir()
    subprocess.run(
        ["git", "init", "--initial-branch", "approved"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "--allow-empty-message", "-m", ""],
        cwd=repo_path,
        check=True,
        capture_output=True,
        env={**os.environ, "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@test.com"}
    )
    return repo_path

@pytest.fixture
def google_doc_id():
    """Return the test Google Doc ID."""
    return "11IKk9cqj7ybfc6aJ6rlBDLC9_l4yE9L094C0m1YDt4g"

@pytest.fixture
def template_doc_id():
    """Return the template Google Doc ID for verify tests."""
    return "1DBskRZBKpolIchljkVowFsvB-xRlSVf8sPguOnxsnhU"

@pytest.fixture
def scheme():
    """Return the Google Docs scheme."""
    return "googledoc_1.0"
```

**Key Implementation Details:**

- **Session-scoped fixture**: `setup_and_cleanup_test_data()` runs once per test session, not per test
- **Automatic `autouse=True`**: This fixture automatically runs before any tests execute
- **Cleanup via yield**: Test data is automatically removed after all tests complete
- **Import requirements**: Fixture requires `PyYAML` (`yaml`) for updating configuration
- **Environment variable**: `THREATWARE_CONFIG_DIR` is set automatically during the test session
- **Verbosity**: Print statements provide visibility into setup/cleanup progress

**Required Dependency:**

Add `PyYAML` to your test requirements:

```bash
pip install pyyaml
```

## Execution Strategy

### Phase 1: Foundation - Verify Actions are Callable (Priority: HIGH)

**Goal**: Establish that convert and verify actions can be invoked from CLI without import or library errors.

1. Set up test infrastructure (conftest.py with minimal fixtures)
2. Create minimal sample threat model YAML file
3. Implement convert action smoke tests
   - Test `threatware convert --help` works
   - Test convert action is available
   - Verify no import errors or missing dependencies
4. Implement verify action smoke tests
   - Test `threatware verify --help` works
   - Test verify action is available
   - Verify no import errors or missing dependencies

### Phase 2: Management Features - Verify Manage Actions are Callable (Priority: HIGH)

**Goal**: Establish that manage.* actions can be invoked from CLI without import or library errors.

1. Set up git repository fixture
2. Implement manage.create action smoke tests
   - Test `threatware manage.create --help` works
   - Test manage.create action is available
   - Verify no import errors or git-related issues
3. Implement manage.indexdata action smoke tests
   - Test `threatware manage.indexdata --help` works
   - Test manage.indexdata action is available
   - Verify no import errors
4. Implement manage.submit action smoke tests
   - Test `threatware manage.submit --help` works
   - Test manage.submit action is available
   - Verify no import errors or git-related issues

**This completes the scope for this phase. Phases 3 and 4 are deferred.**

## Running the Tests

```bash
cd <path-to-threatware-repo>

# Activate the test virtual environment
source .venv-test/bin/activate

# Install test requirements (including PyYAML)
pip install pytest pytest-cov pyyaml

# Run all integration tests
# Note: Test data is automatically set up before tests and cleaned up after
python3 -m pytest test/integration/ -v

# Run specific test file
python3 -m pytest test/integration/test_cli_convert.py -v

# Run specific test with verbose output
python3 -m pytest test/integration/test_cli_convert.py::TestConvertAction::test_convert_action_available -vv

# Run with coverage
python3 -m pytest test/integration/ --cov=threatware --cov-report=html

# Run with detailed setup/cleanup output
python3 -m pytest test/integration/ -v -s

# Deactivate when done
deactivate
```

**What Happens Automatically:**

1. When pytest starts, the `setup_and_cleanup_test_data()` fixture runs automatically (before any tests)
2. Test data directory is created in `test/integration/test_data/`
3. threatware-config is cloned from GitHub
4. Authentication token is copied from `~/.threatware/token.json`
5. Local git repository is created
6. `manage_config.yaml` is updated with local git repo path
7. `THREATWARE_CONFIG_DIR` environment variable is set
8. All tests run with access to the configured test data
9. After all tests complete, the entire `test_data` directory is removed

**No manual setup of test data is required** — it's all handled by pytest fixtures.

## Markers and Fixtures

Use pytest markers to categorize tests:

```python
@pytest.mark.cli          # CLI-based tests
@pytest.mark.integration  # Integration tests
@pytest.mark.convert      # Convert action tests
@pytest.mark.verify       # Verify action tests
@pytest.mark.manage       # Manage action tests
@pytest.mark.e2e          # End-to-end tests
@pytest.mark.slow         # Tests that take longer
@pytest.mark.requires_git # Tests requiring git functionality
```

## Assertions and Validation

### Basic Validation for Smoke Tests

- **Exit Code**: Verify command exits with 0 (no import/execution errors)
- **Stderr Output**: Check stderr for import errors, missing modules, syntax errors
- **Help Output**: Verify help text is returned without errors
- **Action Availability**: Confirm each action is recognized by the CLI
- **No Stack Traces**: Verify no Python tracebacks or segmentation faults

## Integration with CI/CD

Suggested minimal CI configuration:

```yaml
test_integration_phase1_2:
  stage: test
  script:
    - pytest test/integration/test_cli_convert.py -v
    - pytest test/integration/test_cli_verify.py -v
    - pytest test/integration/test_cli_manage.py -v
```

## Known Limitations and Considerations

1. **Limited Scope**: These tests only verify actions are callable without import errors
   - They do NOT validate functional correctness or output structure
   - They do NOT test actual threat model conversion or verification logic
   
2. **Automated Setup**: Test data is automatically created and removed by pytest fixtures
   - No manual setup of test data is required
   - `test_data` directory will be removed after each test run
   - If tests are interrupted, manual cleanup of `test_data` directory may be needed
   
3. **Basic Assertions**: Tests focus on exit codes and error output
   - Complex output validation deferred to future phases

4. **Dedicated Virtual Environment**: Tests run in `.venv-test` separate from main installation
   - This keeps pytest and test dependencies out of the main threatware environment
   - Only required before first test run: `python3 -m venv .venv-test`

5. **PyYAML Dependency**: The conftest.py fixture requires PyYAML for YAML configuration updates
   - Install with: `pip install pyyaml`

## Success Criteria

Tests are successful when:

1. ✅ All smoke tests pass consistently (100% pass rate)
2. ✅ Convert action can be invoked without import errors
3. ✅ Verify action can be invoked without import errors
4. ✅ Manage.create action can be invoked without import errors
5. ✅ Manage.indexdata action can be invoked without import errors
6. ✅ Manage.submit action can be invoked without import errors
7. ✅ Tests run in < 2 minutes total
8. ✅ Tests are isolated and don't interfere with each other
9. ✅ Clear error messages when tests fail

## Next Steps

1. Implement conftest.py with minimal fixtures for CLI invocation
2. Implement smoke tests for convert action (test_cli_convert.py)
3. Implement smoke tests for verify action (test_cli_verify.py)
4. Implement smoke tests for manage actions (test_cli_manage.py)
5. Execute and verify all tests pass
6. Document any import issues found and resolved
