#!/usr/bin/env python3
"""
Integration tests for threatware manage CLI actions.

These tests verify that the manage create, manage indexdata, and manage submit
actions execute successfully with proper git integration.
"""

import pytest
import subprocess
import json
import os


class TestManageActions:
    """Test suite for manage CLI actions."""

    def test_manage_create_help_runs_without_errors(self, threatware_cli):
        """Test that manage create --help runs without import errors."""
        result = subprocess.run(
            threatware_cli + ["manage", "create", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # No Python tracebacks
        assert "Traceback" not in result.stderr
        assert "ModuleNotFoundError" not in result.stderr
        assert "usage" in result.stdout.lower()

    def test_manage_indexdata_help_runs_without_errors(self, threatware_cli):
        """Test that manage indexdata --help runs without import errors."""
        result = subprocess.run(
            threatware_cli + ["manage", "indexdata", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # No Python tracebacks
        assert "Traceback" not in result.stderr
        assert "ModuleNotFoundError" not in result.stderr
        assert "usage" in result.stdout.lower()

    def test_manage_submit_help_runs_without_errors(self, threatware_cli):
        """Test that manage submit --help runs without import errors."""
        result = subprocess.run(
            threatware_cli + ["manage", "submit", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # No Python tracebacks
        assert "Traceback" not in result.stderr
        assert "ModuleNotFoundError" not in result.stderr
        assert "usage" in result.stdout.lower()

    def test_manage_cli_command_exists(self, threatware_cli):
        """Test that manage command exists and is accessible."""
        result = subprocess.run(
            threatware_cli + ["manage", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Manage command should be recognized (return 0 or show help)
        assert "ModuleNotFoundError" not in result.stderr
        assert "usage" in result.stdout.lower()

    def test_manage_actions_workflow(self, threatware_cli, threatware_config_dir, threat_models_repo, google_doc_id, scheme):
        """Test the complete manage workflow: create, indexdata, submit.
        
        This test runs manage actions in sequence as they would be used in practice.
        """
        # Ensure THREATWARE_CONFIG_DIR is set
        env = os.environ.copy()
        env["THREATWARE_CONFIG_DIR"] = threatware_config_dir
        
        # Step 1: Test manage create
        print("\n[Test] Running manage create...")
        result_create = subprocess.run(
            threatware_cli + ["-f", "json", "manage", "create", 
                             "-idprefix", "SSC.TMD",
                             "-s", scheme,
                             "-d", google_doc_id],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        # Should not have import errors
        assert "ModuleNotFoundError" not in result_create.stderr, \
            f"Module import error in manage create: {result_create.stderr}"
        assert "ImportError" not in result_create.stderr, \
            f"Import error in manage create: {result_create.stderr}"
        assert "Traceback" not in result_create.stderr, \
            f"Python exception in manage create: {result_create.stderr}"
        
        # Parse JSON output
        stdout = result_create.stdout.strip()
        if stdout.startswith('threatware v'):
            newline_pos = stdout.find('\n')
            if newline_pos != -1:
                stdout = stdout[newline_pos+1:].strip()
        
        output_create = json.loads(stdout)
        assert "result" in output_create, \
            f"Expected 'result' field in manage create output: {stdout}"
        assert output_create["result"] != "Error", \
            f"manage create failed: {output_create.get('description', output_create.get('result'))}"

        # Capture ID returned from create for downstream steps
        created_id = output_create.get("ID") or output_create.get("id")
        if not created_id and "details" in output_create:
            created_id = output_create["details"].get("ID") or output_create["details"].get("id")
        assert created_id, f"Expected ID in manage create output: {stdout}"
        
        print(f"[Test] manage create successful: {output_create.get('result')}, ID: {created_id}")

        # Merge create branch into approved branch before indexdata
        print("[Test] Merging 'create' branch into 'approved'...")
        git_env = env.copy()
        git_env["GIT_COMMITTER_NAME"] = "Test"
        git_env["GIT_COMMITTER_EMAIL"] = "test@test.com"
        git_env["GIT_AUTHOR_NAME"] = "Test"
        git_env["GIT_AUTHOR_EMAIL"] = "test@test.com"
        subprocess.run(
            ["git", "checkout", "approved"],
            cwd=threat_models_repo,
            check=True,
            capture_output=True,
            env=git_env
        )
        subprocess.run(
            ["git", "merge", "create"],
            cwd=threat_models_repo,
            check=True,
            capture_output=True,
            env=git_env
        )
        print("[Test] Merge complete.")
        
        # Step 2: Test manage indexdata
        print("[Test] Running manage indexdata...")
        result_indexdata = subprocess.run(
            threatware_cli + ["-f", "json", "manage", "indexdata",
                             "-id", created_id],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        # Should not have import errors
        assert "ModuleNotFoundError" not in result_indexdata.stderr, \
            f"Module import error in manage indexdata: {result_indexdata.stderr}"
        assert "ImportError" not in result_indexdata.stderr, \
            f"Import error in manage indexdata: {result_indexdata.stderr}"
        assert "Traceback" not in result_indexdata.stderr, \
            f"Python exception in manage indexdata: {result_indexdata.stderr}"
        
        # Parse JSON output
        stdout = result_indexdata.stdout.strip()
        if stdout.startswith('threatware v'):
            newline_pos = stdout.find('\n')
            if newline_pos != -1:
                stdout = stdout[newline_pos+1:].strip()
        
        # If no stdout, print stderr for debugging
        if not stdout:
            print(f"[Debug] indexdata stderr: {result_indexdata.stderr}")
            raise AssertionError(f"No JSON output from manage indexdata. stderr: {result_indexdata.stderr}")
        
        output_indexdata = json.loads(stdout)
        assert "result" in output_indexdata, \
            f"Expected 'result' field in manage indexdata output: {stdout}"
        assert output_indexdata["result"] == "Success", \
            f"manage indexdata failed: {output_indexdata.get('description', output_indexdata.get('result'))}"

        indexdata_id = output_indexdata.get("ID") or output_indexdata.get("id")
        if not indexdata_id and "details" in output_indexdata:
            indexdata_id = output_indexdata["details"].get("ID") or output_indexdata["details"].get("id")
        assert indexdata_id == created_id, \
            f"manage indexdata returned ID '{indexdata_id}' but expected '{created_id}'"
        
        print(f"[Test] manage indexdata successful: {output_indexdata.get('result')}")
        
        # Step 3: Test manage submit
        print("[Test] Running manage submit...")
        result_submit = subprocess.run(
            threatware_cli + ["-f", "json", "manage", "submit",
                             "-s", scheme,
                             "-d", google_doc_id],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        # Should not have import errors
        assert "ModuleNotFoundError" not in result_submit.stderr, \
            f"Module import error in manage submit: {result_submit.stderr}"
        assert "ImportError" not in result_submit.stderr, \
            f"Import error in manage submit: {result_submit.stderr}"
        assert "Traceback" not in result_submit.stderr, \
            f"Python exception in manage submit: {result_submit.stderr}"
        
        # Parse JSON output
        stdout = result_submit.stdout.strip()
        if stdout.startswith('threatware v'):
            newline_pos = stdout.find('\n')
            if newline_pos != -1:
                stdout = stdout[newline_pos+1:].strip()
        
        output_submit = json.loads(stdout)
        assert "result" in output_submit, \
            f"Expected 'result' field in manage submit output: {stdout}"
        assert output_submit["result"] == "Success", \
            f"manage submit failed: {output_submit.get('description', output_submit.get('result'))}"
        
        print(f"[Test] manage submit successful: {output_submit.get('result')}")
        
        # Verify branch was created in git repo with created_id name
        print(f"[Test] Verifying branch '{created_id}' was created...")
        result_branches = subprocess.run(
            ["git", "branch"],
            cwd=threat_models_repo,
            capture_output=True,
            text=True
        )
        assert created_id in result_branches.stdout, \
            f"Expected branch '{created_id}' not found in git repo. Branches: {result_branches.stdout}"
        print(f"[Test] Branch '{created_id}' verified.")

