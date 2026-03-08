#!/bin/bash
# Test runner for Oracle Users/Groups/Directories property-based tests
# This script runs the property-based tests for Oracle users, groups, and directories configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Oracle Users/Groups/Directories Tests"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "ERROR: pytest is not installed"
    echo "Please install it with: pip install -r requirements.txt"
    exit 1
fi

# Check if VMs are running
echo "Checking if VMs are running..."
cd ..
if ! vagrant status | grep -q "running"; then
    echo "ERROR: VMs are not running"
    echo "Please start VMs with: vagrant up"
    exit 1
fi
cd "$SCRIPT_DIR"

echo "VMs are running. Starting tests..."
echo ""

# Run unit tests first (fast)
echo "=========================================="
echo "Running Unit Tests..."
echo "=========================================="
pytest test_oracle_users_groups_properties.py -v -m unit --tb=short

echo ""
echo "=========================================="
echo "Running Property-Based Tests (100 examples each)..."
echo "=========================================="
echo "WARNING: Property-based tests may take several minutes to complete"
echo ""

# Run property tests with statistics
pytest test_oracle_users_groups_properties.py -v -m property --tb=short --hypothesis-show-statistics

echo ""
echo "=========================================="
echo "All Tests Complete!"
echo "=========================================="
