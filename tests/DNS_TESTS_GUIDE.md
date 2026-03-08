# DNS Configuration Tests - Quick Reference Guide

## Overview

This guide provides quick reference information for running DNS configuration property-based tests for the Oracle RAC Vagrant Setup project.

## Test Files

- **test_dns_properties.py**: Property-based tests for DNS configuration validation
- **run_dns_tests.bat**: Windows test runner script
- **run_dns_tests.sh**: Linux/Mac test runner script

## Prerequisites

### 1. VMs Must Be Running

```bash
# Start VMs
vagrant up

# Check VM status
vagrant status
```

### 2. DNS Must Be Configured

```bash
# Configure dnsmasq on node2
vagrant ssh node2 -c "sudo bash /vagrant/scripts/setup_dnsmasq.sh"

# Verify dnsmasq is running
vagrant ssh node2 -c "systemctl is-active dnsmasq"
```

### 3. Python Dependencies

```bash
# Install test dependencies
pip install -r tests/requirements.txt
```

## Running Tests

### Quick Start (Windows)

```cmd
cd tests
run_dns_tests.bat
```

### Quick Start (Linux/Mac)

```bash
cd tests
./run_dns_tests.sh
```

### Manual Execution

```bash
# Run all DNS tests
pytest tests/test_dns_properties.py -v

# Run specific property test
pytest tests/test_dns_properties.py::test_property_7_dns_service_availability -v
pytest tests/test_dns_properties.py::test_property_8_dns_round_robin -v
pytest tests/test_dns_properties.py::test_property_9_dns_resolution_accuracy -v

# Run with detailed output
pytest tests/test_dns_properties.py -v --tb=short

# Run with coverage
pytest tests/test_dns_properties.py --cov=. --cov-report=html
```

## Property Tests

### Property 7: DNS Service Availability

**Validates**: Requirements 3.1

**Description**: Verifies that dnsmasq is installed and running on at least one RAC node.

**Test Strategy**: 
- Checks all running VMs for dnsmasq installation
- Verifies dnsmasq service is active
- Minimum 100 iterations with different VM combinations

**Example Output**:
```
test_property_7_dns_service_availability PASSED [100 examples]
```

### Property 8: DNS Round Robin

**Validates**: Requirements 3.3

**Description**: Verifies that SCAN name queries return one of three configured IP addresses.

**Test Strategy**:
- Queries rac-scan.localdomain multiple times
- Verifies all returned IPs are in [192.168.1.121, 192.168.1.122, 192.168.1.123]
- Tests round-robin behavior
- Minimum 100 iterations

**Example Output**:
```
test_property_8_dns_round_robin PASSED [100 examples]
```

### Property 9: DNS Resolution Accuracy

**Validates**: Requirements 3.10

**Description**: Verifies that all configured hostnames resolve to correct IP addresses.

**Test Strategy**:
- Tests all hostname-to-IP mappings:
  - Public network: node1.localdomain, node2.localdomain
  - Private network: node1-priv.localdomain, node2-priv.localdomain
  - VIP: node1-vip.localdomain, node2-vip.localdomain
- Minimum 100 iterations with different hostname/VM combinations

**Example Output**:
```
test_property_9_dns_resolution_accuracy PASSED [100 examples]
```

## Unit Tests

In addition to property-based tests, the following unit tests verify specific scenarios:

1. **test_dns_server_node_configuration**: Verifies DNS server is on correct node
2. **test_scan_has_three_ip_addresses**: Verifies SCAN has exactly 3 IPs
3. **test_public_network_hostnames**: Tests public network hostname resolution
4. **test_private_network_hostnames**: Tests private network hostname resolution
5. **test_vip_hostnames**: Tests VIP hostname resolution
6. **test_dnsmasq_configuration_file**: Verifies dnsmasq.conf exists and is correct

## Test Execution Flow

```
┌─────────────────────────────────────────┐
│  1. Check VM Status                     │
│     - Are VMs running?                  │
│     - Skip tests if not                 │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  2. Check DNS Configuration             │
│     - Is dnsmasq running on node2?      │
│     - Skip tests if not                 │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  3. Execute Property Tests              │
│     - Property 7: DNS availability      │
│     - Property 8: Round robin           │
│     - Property 9: Resolution accuracy   │
│     - Each runs 100+ iterations         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  4. Execute Unit Tests                  │
│     - Specific edge cases               │
│     - Configuration validation          │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  5. Report Results                      │
│     - Pass/Fail summary                 │
│     - Skipped tests                     │
│     - Error details                     │
└─────────────────────────────────────────┘
```

## Troubleshooting

### Tests Are Skipped

**Problem**: Tests show as SKIPPED

**Causes**:
1. VMs are not running
2. dnsmasq is not configured

**Solution**:
```bash
# Start VMs
vagrant up

# Configure DNS
vagrant ssh node2 -c "sudo bash /vagrant/scripts/setup_dnsmasq.sh"

# Verify
vagrant status
vagrant ssh node2 -c "systemctl status dnsmasq"
```

### DNS Resolution Fails

**Problem**: test_property_9_dns_resolution_accuracy fails

**Causes**:
1. dnsmasq not running
2. Incorrect dnsmasq configuration
3. Network connectivity issues

**Solution**:
```bash
# Check dnsmasq status
vagrant ssh node2 -c "systemctl status dnsmasq"

# Check dnsmasq logs
vagrant ssh node2 -c "sudo tail -f /var/log/dnsmasq.log"

# Reconfigure dnsmasq
vagrant ssh node2 -c "sudo bash /vagrant/scripts/setup_dnsmasq.sh"

# Test DNS manually
vagrant ssh node1 -c "nslookup node1.localdomain 192.168.1.102"
```

### SCAN Round Robin Not Working

**Problem**: test_property_8_dns_round_robin fails

**Causes**:
1. SCAN entries not configured correctly in dnsmasq.conf
2. Only one SCAN IP is returned

**Solution**:
```bash
# Check dnsmasq configuration
vagrant ssh node2 -c "grep rac-scan /etc/dnsmasq.conf"

# Should show 3 entries:
# address=/rac-scan.localdomain/192.168.1.121
# address=/rac-scan.localdomain/192.168.1.122
# address=/rac-scan.localdomain/192.168.1.123

# Test SCAN resolution manually
vagrant ssh node1 -c "for i in {1..5}; do nslookup rac-scan.localdomain 192.168.1.102; done"
```

### VBoxManage Not Found

**Problem**: Tests fail with "VBoxManage command not found"

**Solution**:
```bash
# Windows: Add VirtualBox to PATH
set PATH=%PATH%;C:\Program Files\Oracle\VirtualBox

# Linux/Mac: Install VirtualBox
# Ubuntu/Debian
sudo apt-get install virtualbox

# macOS
brew install --cask virtualbox
```

## Test Configuration

### Minimum Iterations

All property-based tests run with minimum 100 iterations as specified in the design document.

```python
MIN_ITERATIONS = 100

@settings(max_examples=MIN_ITERATIONS)
@given(...)
def test_property_...():
    ...
```

### Test Timeout

Tests have reasonable timeouts to prevent hanging:
- VM command execution: 30 seconds default
- DNS resolution: 5 seconds per query
- Overall test suite: No hard limit (depends on iteration count)

### Hypothesis Settings

```python
@settings(
    max_examples=MIN_ITERATIONS,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: DNS Configuration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
      
      - name: Run DNS tests (static only)
        run: |
          # Note: Full tests require running VMs
          # In CI, we only validate test syntax
          pytest tests/test_dns_properties.py --collect-only
```

## Performance Considerations

### Test Execution Time

- Property 7 (DNS availability): ~10-20 seconds (100 iterations)
- Property 8 (Round robin): ~30-60 seconds (100 iterations, multiple DNS queries)
- Property 9 (Resolution accuracy): ~60-120 seconds (100 iterations, multiple hostnames)
- Unit tests: ~10-20 seconds total

**Total estimated time**: 2-4 minutes for complete DNS test suite

### Optimization Tips

1. **Run tests in parallel** (if VMs support it):
   ```bash
   pytest tests/test_dns_properties.py -n auto
   ```

2. **Reduce iterations for quick checks**:
   ```bash
   pytest tests/test_dns_properties.py --hypothesis-profile=dev
   ```

3. **Run specific tests only**:
   ```bash
   # Only run property tests
   pytest tests/test_dns_properties.py -k "property"
   
   # Only run unit tests
   pytest tests/test_dns_properties.py -k "test_dns"
   ```

## Additional Resources

- [Main Test README](README.md)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Design Document](../.kiro/specs/oracle-rac-vagrant-setup/design.md)
- [Requirements Document](../.kiro/specs/oracle-rac-vagrant-setup/requirements.md)
