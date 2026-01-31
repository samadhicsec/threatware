#!/usr/bin/env python3
"""
Integration tests for threatware convert CLI action.

These tests verify that the convert action can be invoked without import
or dependency errors when working with Google Docs.
"""

import pytest
import subprocess
import json


class TestConvertAction:
    """Test suite for the convert CLI action."""

    def test_convert_action_available(self, threatware_cli, google_doc_id):
        """Test that convert action is available and executes without errors."""
        result = subprocess.run(
            threatware_cli + ["-f", "json", "convert", "-s", "googledoc_1.0", "-d", google_doc_id],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should not have import errors
        assert "ModuleNotFoundError" not in result.stderr, \
            f"Module import error: {result.stderr}"
        assert "ImportError" not in result.stderr, \
            f"Import error: {result.stderr}"
        
        # Should have JSON output with result field
        # Note: version info goes to stderr, JSON goes to stdout
        try:
            # Skip version line if present at start of stdout
            stdout = result.stdout.strip()
            if stdout.startswith('threatware v'):
                # Find the first newline and skip to next line
                newline_pos = stdout.find('\n')
                if newline_pos != -1:
                    stdout = stdout[newline_pos+1:].strip()
            
            output = json.loads(stdout)
            assert "result" in output, \
                f"Expected 'result' field in output: {stdout}"
            # Test passes as long as result is not Error
            assert output["result"] != "Error", \
                f"Expected valid result, got Error: {output.get('result')}"
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON\nstdout: {repr(result.stdout)}\nstderr: {repr(result.stderr)}\nError: {e}")

    def test_convert_help_runs_without_errors(self, threatware_cli):
        """Test that convert --help runs without import errors."""
        result = subprocess.run(
            threatware_cli + ["convert", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # No Python tracebacks
        assert "Traceback" not in result.stderr
        assert "ModuleNotFoundError" not in result.stderr
        assert "usage" in result.stdout.lower()

    def test_convert_google_doc_produces_valid_json(self, threatware_cli, google_doc_id, scheme):
        """Test that convert produces valid JSON output with result field."""
        result = subprocess.run(
            threatware_cli + ["-f", "json", "convert", "-s", scheme, "-d", google_doc_id],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check for import/compilation errors
        assert "ModuleNotFoundError" not in result.stderr, \
            f"Module import error in convert: {result.stderr}"
        assert "ImportError" not in result.stderr, \
            f"Import error in convert: {result.stderr}"
        
        # Parse JSON and verify result field
        # Note: version info goes to stderr, JSON goes to stdout
        try:
            # Skip version line if present at start of stdout
            stdout = result.stdout.strip()
            if stdout.startswith('threatware v'):
                # Find the first newline and skip to next line
                newline_pos = stdout.find('\n')
                if newline_pos != -1:
                    stdout = stdout[newline_pos+1:].strip()
            
            output = json.loads(stdout)
            assert "result" in output, \
                f"Expected 'result' field in JSON output: {stdout}"
            # Test passes as long as result is not Error
            assert output["result"] != "Error", \
                f"Expected valid result, got Error: {output.get('result')}"
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON\nstdout: {repr(result.stdout)}\nstderr: {repr(result.stderr)}\nError: {e}")

    def test_convert_cli_command_exists(self, threatware_cli):
        """Test that threatware CLI command itself can be invoked."""
        result = subprocess.run(
            threatware_cli + ["--help"],
            capture_output=True,
            text=True
        )
        
        # Should not have import errors
        assert "ModuleNotFoundError" not in result.stderr
        assert "ImportError" not in result.stderr
        
        # Should have meaningful output
        assert result.returncode == 0 or len(result.stdout) > 0

