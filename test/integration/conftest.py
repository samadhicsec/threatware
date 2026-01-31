#!/usr/bin/env python3
"""
Pytest configuration and fixtures for threatware integration tests.
"""

import pytest
import subprocess
import shutil
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


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
    
    # Step 2: Copy authentication files
    threatware_home = Path.home() / ".threatware"
    
    # Copy token.json
    token_src = threatware_home / "token.json"
    token_dst = THREATWARE_CONFIG_CLONE_DIR / "token.json"
    if token_src.exists():
        print(f"[Setup] Copying token.json to cloned repo")
        shutil.copy2(token_src, token_dst)
    else:
        print(f"[Setup] Warning: token.json not found at {token_src}")
    
    # Copy credentials.json
    credentials_src = threatware_home / "credentials.json"
    credentials_dst = THREATWARE_CONFIG_CLONE_DIR / "credentials.json"
    if credentials_src.exists():
        print(f"[Setup] Copying credentials.json to cloned repo")
        shutil.copy2(credentials_src, credentials_dst)
    else:
        print(f"[Setup] Warning: credentials.json not found at {credentials_src}")
    
    # Step 3: Create local git repository for threat models
    print(f"[Setup] Creating local threat models git repository at {THREAT_MODELS_REPO_DIR}")
    if THREAT_MODELS_REPO_DIR.exists():
        shutil.rmtree(THREAT_MODELS_REPO_DIR)
    THREAT_MODELS_REPO_DIR.mkdir(parents=True, exist_ok=True)
    
    env = os.environ.copy()
    env["GIT_COMMITTER_NAME"] = "Test"
    env["GIT_COMMITTER_EMAIL"] = "test@test.com"
    env["GIT_AUTHOR_NAME"] = "Test"
    env["GIT_AUTHOR_EMAIL"] = "test@test.com"
    
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
        env=env
    )
    
    # Step 4: Update manage_config.yaml with local git repository path using sed
    manage_config_file = THREATWARE_CONFIG_CLONE_DIR / "manage" / "manage_config.yaml"
    if manage_config_file.exists():
        print(f"[Setup] Updating manage_config.yaml with local git repo path")
        # Use sed to replace the remote path in the YAML file
        # This avoids YAML parsing issues with the config file's complex structure
        subprocess.run(
            ["sed", "-i", f"s|remote:.*|remote: file://{THREAT_MODELS_REPO_DIR}|g", 
             str(manage_config_file)],
            check=True,
            capture_output=True
        )
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
    """Return the threatware config directory path for manage tests."""
    return str(THREATWARE_CONFIG_CLONE_DIR)


@pytest.fixture
def threat_models_repo():
    """Return the local threat models git repository path."""
    return str(THREAT_MODELS_REPO_DIR)


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


@pytest.fixture
def isolated_git_repo(tmp_path):
    """Create isolated git repo for manage command tests.
    
    Args:
        tmp_path: pytest temporary directory fixture
        
    Returns:
        Path to the isolated git repository
    """
    repo_path = tmp_path / "threatmodels"
    repo_path.mkdir()
    
    # Initialize git repo with approved branch
    subprocess.run(
        ["git", "init", "--initial-branch", "approved"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )
    
    # Create initial commit
    env = os.environ.copy()
    env["GIT_COMMITTER_NAME"] = "Test"
    env["GIT_COMMITTER_EMAIL"] = "test@test.com"
    env["GIT_AUTHOR_NAME"] = "Test"
    env["GIT_AUTHOR_EMAIL"] = "test@test.com"
    
    subprocess.run(
        ["git", "commit", "--allow-empty", "--allow-empty-message", "-m", ""],
        cwd=repo_path,
        check=True,
        capture_output=True,
        env=env
    )
    
    return repo_path
