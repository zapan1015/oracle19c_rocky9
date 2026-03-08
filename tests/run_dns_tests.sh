#!/bin/bash
#
# DNS Configuration Property-Based Tests Runner
# Oracle 19c RAC 2-Node Cluster Setup
#
# This script runs DNS configuration validation tests
# Tests execute commands inside Linux VMs via vagrant ssh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "DNS Configuration Tests"
echo "========================================"
echo ""

# Check if VMs are running
echo "Checking VM status..."
if ! vagrant status | grep -q "running"; then
    echo -e "${YELLOW}[WARNING]${NC} VMs are not running. Some tests will be skipped."
    echo "Run 'vagrant up' to start VMs before running tests."
    echo ""
fi

# Check if dnsmasq is configured
echo "Checking DNS configuration..."
if ! vagrant ssh node2 -c "systemctl is-active dnsmasq" >/dev/null 2>&1; then
    echo -e "${YELLOW}[WARNING]${NC} dnsmasq is not running on node2."
    echo "Run 'vagrant ssh node2 -c \"sudo bash /vagrant/scripts/setup_dnsmasq.sh\"' to configure DNS."
    echo ""
fi

echo "Running DNS property-based tests..."
echo ""

# Run tests
python -m pytest tests/test_dns_properties.py -v --tb=short

echo ""
echo "========================================"
echo "Test execution completed"
echo "========================================"
