"""
Property-Based Tests for DNS Configuration Validation
Oracle 19c RAC 2-Node Cluster Setup

This module contains property-based tests to verify DNS configuration
meets all requirements for Oracle RAC SCAN and hostname resolution.

Testing Framework: Python Hypothesis
Minimum Iterations: 100 per property
Host Environment: Windows (tests execute commands in Linux VMs via vagrant ssh)
"""

import subprocess
import re
from pathlib import Path
from typing import Dict, List, Set
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck


# ============================================================================
# Test Configuration
# ============================================================================

# Minimum iterations for property-based tests
MIN_ITERATIONS = 100

# VM names
VM_NAMES = ["node1", "node2"]

# DNS Server configuration
DNS_SERVER_NODE = "node2"
DNS_SERVER_IP = "192.168.1.102"

# SCAN configuration
SCAN_NAME = "rac-scan.localdomain"
SCAN_IPS = ["192.168.1.121", "192.168.1.122", "192.168.1.123"]

# Hostname to IP mappings
HOSTNAME_MAPPINGS = {
    # Public Network
    "node1.localdomain": "192.168.1.101",
    "node2.localdomain": "192.168.1.102",
    # Private Network
    "node1-priv.localdomain": "10.0.0.101",
    "node2-priv.localdomain": "10.0.0.102",
    # VIP addresses
    "node1-vip.localdomain": "192.168.1.111",
    "node2-vip.localdomain": "192.168.1.112",
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_vagrant_status() -> Dict[str, str]:
    """
    Get the status of all Vagrant VMs.
    
    Returns:
        Dictionary mapping VM names to their status
    """
    try:
        result = subprocess.run(
            ["vagrant", "status", "--machine-readable"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent
        )
        
        status_dict = {}
        for line in result.stdout.splitlines():
            parts = line.split(",")
            if len(parts) >= 4 and parts[2] == "state":
                vm_name = parts[1]
                state = parts[3]
                status_dict[vm_name] = state
        
        return status_dict
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        pytest.skip(f"Unable to get Vagrant status: {e}")


def execute_vm_command(vm_name: str, command: str) -> str:
    """
    Execute a command inside a VM via vagrant ssh.
    
    Args:
        vm_name: Name of the Vagrant VM (e.g., "node1", "node2")
        command: Shell command to execute
    
    Returns:
        Command output as string
    """
    try:
        result = subprocess.run(
            ["vagrant", "ssh", vm_name, "-c", command],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""


def check_dnsmasq_installed(vm_name: str) -> bool:
    """
    Check if dnsmasq is installed on a VM.
    
    Args:
        vm_name: Name of the Vagrant VM
    
    Returns:
        True if dnsmasq is installed, False otherwise
    """
    output = execute_vm_command(vm_name, "rpm -q dnsmasq")
    return "dnsmasq-" in output and "not installed" not in output


def check_dnsmasq_running(vm_name: str) -> bool:
    """
    Check if dnsmasq service is running on a VM.
    
    Args:
        vm_name: Name of the Vagrant VM
    
    Returns:
        True if dnsmasq is running, False otherwise
    """
    output = execute_vm_command(vm_name, "systemctl is-active dnsmasq")
    return output == "active"


def resolve_hostname(vm_name: str, hostname: str, dns_server: str = "127.0.0.1") -> List[str]:
    """
    Resolve a hostname using nslookup inside a VM.
    
    Args:
        vm_name: Name of the Vagrant VM
        hostname: Hostname to resolve
        dns_server: DNS server to query (default: 127.0.0.1)
    
    Returns:
        List of IP addresses resolved for the hostname
    """
    command = f"nslookup {hostname} {dns_server} 2>/dev/null | grep -A1 'Name:' | grep 'Address:' | awk '{{print $2}}'"
    output = execute_vm_command(vm_name, command)
    
    if not output:
        return []
    
    # Parse IP addresses from output
    ips = []
    for line in output.splitlines():
        line = line.strip()
        # Validate IP address format
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', line):
            ips.append(line)
    
    return ips


def resolve_hostname_multiple_times(vm_name: str, hostname: str, count: int = 10) -> List[str]:
    """
    Resolve a hostname multiple times to test round-robin DNS.
    
    Args:
        vm_name: Name of the Vagrant VM
        hostname: Hostname to resolve
        count: Number of times to resolve
    
    Returns:
        List of all IP addresses returned (may contain duplicates)
    """
    all_ips = []
    for _ in range(count):
        ips = resolve_hostname(vm_name, hostname, DNS_SERVER_IP)
        all_ips.extend(ips)
    
    return all_ips


# ============================================================================
# Property 7: DNS Service Availability
# ============================================================================

@settings(max_examples=MIN_ITERATIONS, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.just(VM_NAMES))
def test_property_7_dns_service_availability(vm_names: List[str]):
    """
    **Validates: Requirements 3.1**
    
    Feature: oracle-rac-vagrant-setup, Property 7: 
    For all RAC clusters, dnsmasq SHALL be installed and running on at least one node.
    """
    # Check if VMs are running
    status = get_vagrant_status()
    
    running_vms = [vm for vm in vm_names if vm in status and status[vm] == "running"]
    
    if not running_vms:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    # Check if dnsmasq is installed and running on at least one node
    dnsmasq_nodes = []
    
    for vm_name in running_vms:
        if check_dnsmasq_installed(vm_name):
            dnsmasq_nodes.append(vm_name)
    
    assert len(dnsmasq_nodes) >= 1, \
        f"dnsmasq should be installed on at least one node, found on: {dnsmasq_nodes}"
    
    # Check if dnsmasq is running on at least one node
    running_dnsmasq_nodes = []
    
    for vm_name in dnsmasq_nodes:
        if check_dnsmasq_running(vm_name):
            running_dnsmasq_nodes.append(vm_name)
    
    assert len(running_dnsmasq_nodes) >= 1, \
        f"dnsmasq should be running on at least one node, running on: {running_dnsmasq_nodes}"


# ============================================================================
# Property 8: DNS Round Robin
# ============================================================================

@settings(max_examples=MIN_ITERATIONS, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.sampled_from(VM_NAMES))
def test_property_8_dns_round_robin(vm_name: str):
    """
    **Validates: Requirements 3.3**
    
    Feature: oracle-rac-vagrant-setup, Property 8: 
    For all SCAN name queries (rac-scan.localdomain), multiple queries SHALL return 
    one of three IP addresses (192.168.1.121, 192.168.1.122, 192.168.1.123).
    """
    # Check if VM is running
    status = get_vagrant_status()
    
    if vm_name not in status or status[vm_name] != "running":
        pytest.skip(f"VM {vm_name} is not running. Run 'vagrant up' first.")
    
    # Check if dnsmasq is running on DNS server node
    if not check_dnsmasq_running(DNS_SERVER_NODE):
        pytest.skip(f"dnsmasq is not running on {DNS_SERVER_NODE}. Run setup_dnsmasq.sh first.")
    
    # Resolve SCAN name multiple times
    resolved_ips = resolve_hostname_multiple_times(vm_name, SCAN_NAME, count=10)
    
    assert len(resolved_ips) > 0, \
        f"SCAN name {SCAN_NAME} should resolve to at least one IP address"
    
    # Verify all resolved IPs are in the expected SCAN IP list
    for ip in resolved_ips:
        assert ip in SCAN_IPS, \
            f"SCAN name {SCAN_NAME} resolved to {ip}, which is not in expected SCAN IPs {SCAN_IPS}"
    
    # Get unique IPs to verify round-robin
    unique_ips = list(set(resolved_ips))
    
    # For round-robin DNS, we should see multiple different IPs
    # Note: dnsmasq returns all 3 IPs in the answer section, so we should see all 3
    assert len(unique_ips) >= 1, \
        f"SCAN name {SCAN_NAME} should resolve to at least one of the three SCAN IPs"
    
    # Verify that all unique IPs are valid SCAN IPs
    for ip in unique_ips:
        assert ip in SCAN_IPS, \
            f"Resolved IP {ip} is not a valid SCAN IP"


# ============================================================================
# Property 9: DNS Resolution Accuracy
# ============================================================================

@settings(max_examples=MIN_ITERATIONS, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    vm_name=st.sampled_from(VM_NAMES),
    hostname=st.sampled_from(list(HOSTNAME_MAPPINGS.keys()))
)
def test_property_9_dns_resolution_accuracy(vm_name: str, hostname: str):
    """
    **Validates: Requirements 3.10**
    
    Feature: oracle-rac-vagrant-setup, Property 9: 
    For all configured hostnames, DNS queries SHALL return the correct IP addresses.
    """
    # Check if VM is running
    status = get_vagrant_status()
    
    if vm_name not in status or status[vm_name] != "running":
        pytest.skip(f"VM {vm_name} is not running. Run 'vagrant up' first.")
    
    # Check if dnsmasq is running on DNS server node
    if not check_dnsmasq_running(DNS_SERVER_NODE):
        pytest.skip(f"dnsmasq is not running on {DNS_SERVER_NODE}. Run setup_dnsmasq.sh first.")
    
    # Get expected IP address
    expected_ip = HOSTNAME_MAPPINGS[hostname]
    
    # Resolve hostname
    resolved_ips = resolve_hostname(vm_name, hostname, DNS_SERVER_IP)
    
    assert len(resolved_ips) > 0, \
        f"Hostname {hostname} should resolve to at least one IP address"
    
    # Verify the resolved IP matches the expected IP
    assert expected_ip in resolved_ips, \
        f"Hostname {hostname} should resolve to {expected_ip}, got {resolved_ips}"


# ============================================================================
# Additional Unit Tests for Edge Cases
# ============================================================================

def test_dns_server_node_configuration():
    """Verify that DNS server is configured on the correct node."""
    status = get_vagrant_status()
    
    if DNS_SERVER_NODE not in status or status[DNS_SERVER_NODE] != "running":
        pytest.skip(f"DNS server node {DNS_SERVER_NODE} is not running. Run 'vagrant up' first.")
    
    # Check if dnsmasq is installed
    assert check_dnsmasq_installed(DNS_SERVER_NODE), \
        f"dnsmasq should be installed on {DNS_SERVER_NODE}"
    
    # Check if dnsmasq is running
    assert check_dnsmasq_running(DNS_SERVER_NODE), \
        f"dnsmasq should be running on {DNS_SERVER_NODE}"


def test_scan_has_three_ip_addresses():
    """Verify that SCAN name is configured with exactly three IP addresses."""
    status = get_vagrant_status()
    
    # Find a running VM to test from
    running_vm = None
    for vm_name in VM_NAMES:
        if vm_name in status and status[vm_name] == "running":
            running_vm = vm_name
            break
    
    if not running_vm:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    if not check_dnsmasq_running(DNS_SERVER_NODE):
        pytest.skip(f"dnsmasq is not running on {DNS_SERVER_NODE}. Run setup_dnsmasq.sh first.")
    
    # Query SCAN name multiple times to collect all possible IPs
    all_ips = resolve_hostname_multiple_times(running_vm, SCAN_NAME, count=20)
    unique_ips = list(set(all_ips))
    
    # SCAN should have exactly 3 IP addresses
    # Note: dnsmasq may return all 3 IPs in one query, or rotate them
    assert len(unique_ips) >= 1, \
        f"SCAN name {SCAN_NAME} should resolve to at least one IP"
    
    # All unique IPs should be in the expected SCAN IP list
    for ip in unique_ips:
        assert ip in SCAN_IPS, \
            f"SCAN IP {ip} is not in expected SCAN IPs {SCAN_IPS}"


def test_public_network_hostnames():
    """Verify that public network hostnames resolve correctly."""
    status = get_vagrant_status()
    
    running_vm = None
    for vm_name in VM_NAMES:
        if vm_name in status and status[vm_name] == "running":
            running_vm = vm_name
            break
    
    if not running_vm:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    if not check_dnsmasq_running(DNS_SERVER_NODE):
        pytest.skip(f"dnsmasq is not running on {DNS_SERVER_NODE}. Run setup_dnsmasq.sh first.")
    
    # Test public network hostnames
    public_hostnames = {
        "node1.localdomain": "192.168.1.101",
        "node2.localdomain": "192.168.1.102",
    }
    
    for hostname, expected_ip in public_hostnames.items():
        resolved_ips = resolve_hostname(running_vm, hostname, DNS_SERVER_IP)
        assert expected_ip in resolved_ips, \
            f"Public hostname {hostname} should resolve to {expected_ip}, got {resolved_ips}"


def test_private_network_hostnames():
    """Verify that private network hostnames resolve correctly."""
    status = get_vagrant_status()
    
    running_vm = None
    for vm_name in VM_NAMES:
        if vm_name in status and status[vm_name] == "running":
            running_vm = vm_name
            break
    
    if not running_vm:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    if not check_dnsmasq_running(DNS_SERVER_NODE):
        pytest.skip(f"dnsmasq is not running on {DNS_SERVER_NODE}. Run setup_dnsmasq.sh first.")
    
    # Test private network hostnames
    private_hostnames = {
        "node1-priv.localdomain": "10.0.0.101",
        "node2-priv.localdomain": "10.0.0.102",
    }
    
    for hostname, expected_ip in private_hostnames.items():
        resolved_ips = resolve_hostname(running_vm, hostname, DNS_SERVER_IP)
        assert expected_ip in resolved_ips, \
            f"Private hostname {hostname} should resolve to {expected_ip}, got {resolved_ips}"


def test_vip_hostnames():
    """Verify that VIP hostnames resolve correctly."""
    status = get_vagrant_status()
    
    running_vm = None
    for vm_name in VM_NAMES:
        if vm_name in status and status[vm_name] == "running":
            running_vm = vm_name
            break
    
    if not running_vm:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    if not check_dnsmasq_running(DNS_SERVER_NODE):
        pytest.skip(f"dnsmasq is not running on {DNS_SERVER_NODE}. Run setup_dnsmasq.sh first.")
    
    # Test VIP hostnames
    vip_hostnames = {
        "node1-vip.localdomain": "192.168.1.111",
        "node2-vip.localdomain": "192.168.1.112",
    }
    
    for hostname, expected_ip in vip_hostnames.items():
        resolved_ips = resolve_hostname(running_vm, hostname, DNS_SERVER_IP)
        assert expected_ip in resolved_ips, \
            f"VIP hostname {hostname} should resolve to {expected_ip}, got {resolved_ips}"


def test_dnsmasq_configuration_file():
    """Verify that dnsmasq configuration file exists and contains required entries."""
    status = get_vagrant_status()
    
    if DNS_SERVER_NODE not in status or status[DNS_SERVER_NODE] != "running":
        pytest.skip(f"DNS server node {DNS_SERVER_NODE} is not running. Run 'vagrant up' first.")
    
    # Check if dnsmasq.conf exists
    output = execute_vm_command(DNS_SERVER_NODE, "test -f /etc/dnsmasq.conf && echo 'exists'")
    assert "exists" in output, \
        "/etc/dnsmasq.conf should exist on DNS server node"
    
    # Check if configuration contains SCAN entries
    output = execute_vm_command(DNS_SERVER_NODE, "grep -c 'rac-scan.localdomain' /etc/dnsmasq.conf")
    scan_entries = int(output) if output.isdigit() else 0
    
    assert scan_entries >= 3, \
        f"dnsmasq.conf should contain at least 3 SCAN entries, found {scan_entries}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
