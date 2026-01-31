#!/bin/bash
# Integration test runner for threatware

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=============================================="
echo "Threatware Integration Test Runner"
echo "=============================================="
echo ""

# Check if .venv-test exists
if [ ! -d "$REPO_ROOT/.venv-test" ]; then
    echo "Error: .venv-test virtual environment not found at $REPO_ROOT/.venv-test"
    echo ""
    echo "Please create it first with:"
    echo "  cd $REPO_ROOT"
    echo "  python3 -m venv .venv-test"
    echo "  source .venv-test/bin/activate"
    echo "  pip install pytest pytest-cov pyyaml"
    exit 1
fi

# Navigate to repo root
cd "$REPO_ROOT"

# Activate the test virtual environment
source .venv-test/bin/activate

echo "✓ Test virtual environment activated (.venv-test)"
echo ""

# Run all integration tests
TEST_PATH="test/integration/"

echo "Running all integration tests from: $TEST_PATH"
echo ""

# Run pytest with verbose output
python3 -m pytest "$TEST_PATH" -v --tb=short

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "=============================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed (exit code: $TEST_EXIT_CODE)"
fi
echo "=============================================="

# Deactivate virtual environment
deactivate

exit $TEST_EXIT_CODE
