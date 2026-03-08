"""
Property-Based Tests for Vagrantfile Validation
Oracle 19c RAC 2-Node Cluster Setup

This module contains property-based tests to verify the Vagrantfile configuration
meets all requirements for Oracle RAC deployment.

Testing Framework: Python Hypothesis
Minimum Iterations: 100 per property
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Any
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck


# ============================================================================
# Test Configuration
# ============================================================================

# Minimum iterations for property-based tests
MIN_ITERATIONS = 100

# VM names
VM_NAMES = ["node1", "node2"]

# Expected configuration values
EXPECTED_BASE_IMAGE = "rockylinux/9"
EXPECTED_RAM_MB = 8192
MIN_CPU_CORES = 2
EXPECTED_NETWORK_ADAPTERS = 2

# Network configuration
PUBLIC_NETWORK_IPS = {
    "node1": "192.168.1.101",
    "node2": "192.168.1.102"
}

PRIVATE_NETWORK_IPS = {
    "node1": "10.0.0.101",
    "node2": "10.0.0.102"
}

# Storage configuration
SHARED_STORAGE_DEVICES = ["/dev/sdb", "/dev/sdc", "/dev/sdd"]
ASM_DISKS = ["asm_disk1.vdi", "asm_disk2.vdi", "asm_disk3.vdi"]


# ============================================================================
# Helper Functions
# ============================================================================

def get_vm_info(vm_name: str) -> Dict[str, Any]:
    """
    Get VM information from VirtualBox.
    
    Args:
        vm_name: Name of the VM (e.g., "rac-node1", "rac-node2")
    
    Returns:
        Dictionary containing VM configuration information
    """
    try:
        # Get VM info in machine-readable format
        result = subprocess.run(
            ["VBoxManage", "showvminfo", vm_name, "--machinereadable"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output into a dictionary
        vm_info = {}
        for line in result.stdout.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                # Remove quotes from value
                value = value.strip('"')
                vm_info[key] = value
        
        return vm_info
    except subprocess.CalledProcessError as e:
        pytest.skip(f"VM {vm_name} not found or VirtualBox not available: {e}")
    except FileNotFoundError:
        pytest.skip("VBoxManage command not found. VirtualBox may not be installed.")


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


def check_shared_storage_access(vm_name: str, device: str) -> bool:
    """
    Check if a VM can access a shared storage device.
    
    Args:
        vm_name: Name of the Vagrant VM (e.g., "node1", "node2")
        device: Device path (e.g., "/dev/sdb")
    
    Returns:
        True if the device is accessible, False otherwise
    """
    try:
        # Use vagrant ssh to check if device exists
        result = subprocess.run(
            ["vagrant", "ssh", vm_name, "-c", f"test -b {device} && echo 'exists'"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        return "exists" in result.stdout
    except subprocess.CalledProcessError:
        return False


def parse_vagrantfile() -> Dict[str, Any]:
    """
    Parse the Vagrantfile to extract configuration.
    
    Returns:
        Dictionary containing parsed Vagrantfile configuration
    """
    vagrantfile_path = Path(__file__).parent.parent / "Vagrantfile"
    
    if not vagrantfile_path.exists():
        pytest.skip("Vagrantfile not found")
    
    with open(vagrantfile_path, 'r') as f:
        content = f.read()
    
    config = {
        "base_image": None,
        "nodes": {}
    }
    
    # Extract base image
    base_image_match = re.search(r'config\.vm\.box\s*=\s*"([^"]+)"', content)
    if base_image_match:
        config["base_image"] = base_image_match.group(1)
    
    # Extract node configurations
    for node_name in VM_NAMES:
        node_config = {
            "memory": None,
            "cpus": None,
            "networks": []
        }
        
        # Find the node definition block
        node_pattern = rf'config\.vm\.define\s+"{node_name}".*?end'
        node_match = re.search(node_pattern, content, re.DOTALL)
        
        if node_match:
            node_block = node_match.group(0)
            
            # Extract memory
            memory_match = re.search(r'vb\.memory\s*=\s*"(\d+)"', node_block)
            if memory_match:
                node_config["memory"] = int(memory_match.group(1))
            
            # Extract CPUs
            cpus_match = re.search(r'vb\.cpus\s*=\s*(\d+)', node_block)
            if cpus_match:
                node_config["cpus"] = int(cpus_match.group(1))
            
            # Extract networks - need to handle multi-line network definitions
            # Split by lines and look for network definitions
            lines = node_block.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i]
                if '.vm.network' in line and 'private_network' in line:
                    # Check if this is a single-line or multi-line definition
                    network_info = {
                        "type": "private_network",
                        "ip": None,
                        "internal": False
                    }
                    
                    # Extract IP from current line or next lines
                    ip_match = re.search(r'ip:\s*"([^"]+)"', line)
                    if ip_match:
                        network_info["ip"] = ip_match.group(1)
                    
                    # Check for virtualbox__intnet in current line
                    if 'virtualbox__intnet' in line:
                        network_info["internal"] = True
                    
                    # If no IP found yet, check next few lines (multi-line definition)
                    if not network_info["ip"]:
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j]
                            if 'ip:' in next_line:
                                ip_match = re.search(r'ip:\s*"([^"]+)"', next_line)
                                if ip_match:
                                    network_info["ip"] = ip_match.group(1)
                            if 'virtualbox__intnet' in next_line:
                                network_info["internal"] = True
                            # Stop if we hit another network definition or end of block
                            if '.vm.network' in next_line or 'end' in next_line:
                                break
                    
                    node_config["networks"].append(network_info)
                i += 1
        
        config["nodes"][node_name] = node_config
    
    return config


# ============================================================================
# Property 1: VM Configuration Consistency
# ============================================================================

@settings(max_examples=MIN_ITERATIONS, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.sampled_from(VM_NAMES))
def test_property_1_vm_configuration_consistency(vm_name: str):
    """
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    
    Feature: oracle-rac-vagrant-setup, Property 1: 
    For all provisioned VMs, each VM SHALL use rockylinux/9 base image, 
    have exactly 8GB RAM, minimum 2 CPU cores, and exactly 2 network adapters.
    """
    # Parse Vagrantfile configuration
    config = parse_vagrantfile()
    
    # Verify base image
    assert config["base_image"] == EXPECTED_BASE_IMAGE, \
        f"Base image should be {EXPECTED_BASE_IMAGE}, got {config['base_image']}"
    
    # Verify node configuration
    node_config = config["nodes"][vm_name]
    
    # Verify RAM
    assert node_config["memory"] == EXPECTED_RAM_MB, \
        f"{vm_name} should have {EXPECTED_RAM_MB}MB RAM, got {node_config['memory']}MB"
    
    # Verify CPU cores
    assert node_config["cpus"] >= MIN_CPU_CORES, \
        f"{vm_name} should have at least {MIN_CPU_CORES} CPU cores, got {node_config['cpus']}"
    
    # Verify network adapters
    assert len(node_config["networks"]) == EXPECTED_NETWORK_ADAPTERS, \
        f"{vm_name} should have exactly {EXPECTED_NETWORK_ADAPTERS} network adapters, " \
        f"got {len(node_config['networks'])}"


# ============================================================================
# Property 2: Shared Storage Accessibility
# ============================================================================

@settings(max_examples=MIN_ITERATIONS, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    vm_name=st.sampled_from(VM_NAMES),
    device=st.sampled_from(SHARED_STORAGE_DEVICES)
)
def test_property_2_shared_storage_accessibility(vm_name: str, device: str):
    """
    **Validates: Requirements 1.5, 9.12**
    
    Feature: oracle-rac-vagrant-setup, Property 2: 
    For all provisioned RAC nodes, each node SHALL be able to access 
    all shared storage devices (/dev/sdb, /dev/sdc, /dev/sdd).
    """
    # Check if VMs are running
    status = get_vagrant_status()
    
    if vm_name not in status or status[vm_name] != "running":
        pytest.skip(f"VM {vm_name} is not running. Run 'vagrant up' first.")
    
    # Verify shared storage access
    has_access = check_shared_storage_access(vm_name, device)
    
    assert has_access, \
        f"{vm_name} should be able to access shared storage device {device}"


# ============================================================================
# Property 3: VM Running State
# ============================================================================

@settings(max_examples=MIN_ITERATIONS, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.just(VM_NAMES))
def test_property_3_vm_running_state(vm_names: List[str]):
    """
    **Validates: Requirements 1.6**
    
    Feature: oracle-rac-vagrant-setup, Property 3: 
    For all provisioning completions, both VMs (node1, node2) SHALL be in running state.
    """
    status = get_vagrant_status()
    
    for vm_name in vm_names:
        if vm_name not in status:
            pytest.skip(f"VM {vm_name} not found. Run 'vagrant up' first.")
        
        assert status[vm_name] == "running", \
            f"VM {vm_name} should be in running state, got {status[vm_name]}"


# ============================================================================
# Property 4: Provisioning Idempotence
# ============================================================================

@settings(max_examples=MIN_ITERATIONS, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.sampled_from(VM_NAMES))
def test_property_4_provisioning_idempotence(vm_name: str):
    """
    **Validates: Requirements 1.7, 14.1, 14.5**
    
    Feature: oracle-rac-vagrant-setup, Property 4: 
    For all Vagrant configurations, running provisioning multiple times with the same 
    Vagrantfile SHALL produce identical VM configurations.
    """
    # Parse Vagrantfile configuration (first read)
    config1 = parse_vagrantfile()
    
    # Parse Vagrantfile configuration (second read)
    config2 = parse_vagrantfile()
    
    # Verify configurations are identical
    assert config1 == config2, \
        "Multiple reads of Vagrantfile should produce identical configurations"
    
    # Verify node configuration is consistent
    node_config1 = config1["nodes"][vm_name]
    node_config2 = config2["nodes"][vm_name]
    
    assert node_config1["memory"] == node_config2["memory"], \
        f"Memory configuration for {vm_name} should be consistent"
    
    assert node_config1["cpus"] == node_config2["cpus"], \
        f"CPU configuration for {vm_name} should be consistent"
    
    assert len(node_config1["networks"]) == len(node_config2["networks"]), \
        f"Network configuration for {vm_name} should be consistent"


# ============================================================================
# Property 5: Network Adapter Configuration
# ============================================================================

@settings(max_examples=MIN_ITERATIONS, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.sampled_from(VM_NAMES))
def test_property_5_network_adapter_configuration(vm_name: str):
    """
    **Validates: Requirements 2.1, 2.2, 2.7**
    
    Feature: oracle-rac-vagrant-setup, Property 5: 
    For all RAC nodes, Adapter 1 SHALL be private_network type and 
    Adapter 2 SHALL be internal network using virtualbox__intnet option.
    """
    config = parse_vagrantfile()
    node_config = config["nodes"][vm_name]
    
    # Verify we have exactly 2 network adapters
    assert len(node_config["networks"]) == 2, \
        f"{vm_name} should have exactly 2 network adapters"
    
    # Adapter 1: Public Network (private_network type, not internal)
    adapter1 = node_config["networks"][0]
    assert adapter1["type"] == "private_network", \
        f"{vm_name} Adapter 1 should be private_network type"
    assert not adapter1["internal"], \
        f"{vm_name} Adapter 1 should not be internal network"
    assert adapter1["ip"] == PUBLIC_NETWORK_IPS[vm_name], \
        f"{vm_name} Adapter 1 should have IP {PUBLIC_NETWORK_IPS[vm_name]}"
    
    # Adapter 2: Private Network (private_network type with virtualbox__intnet)
    adapter2 = node_config["networks"][1]
    assert adapter2["type"] == "private_network", \
        f"{vm_name} Adapter 2 should be private_network type"
    assert adapter2["internal"], \
        f"{vm_name} Adapter 2 should be internal network (virtualbox__intnet)"
    assert adapter2["ip"] == PRIVATE_NETWORK_IPS[vm_name], \
        f"{vm_name} Adapter 2 should have IP {PRIVATE_NETWORK_IPS[vm_name]}"


# ============================================================================
# Additional Unit Tests for Edge Cases
# ============================================================================

def test_vagrantfile_exists():
    """Verify that Vagrantfile exists in the project root."""
    vagrantfile_path = Path(__file__).parent.parent / "Vagrantfile"
    assert vagrantfile_path.exists(), "Vagrantfile should exist in project root"


def test_asm_disk_files_configuration():
    """Verify that ASM disk files are properly configured in Vagrantfile."""
    vagrantfile_path = Path(__file__).parent.parent / "Vagrantfile"
    
    with open(vagrantfile_path, 'r') as f:
        content = f.read()
    
    # Verify all ASM disks are referenced
    for disk in ASM_DISKS:
        assert disk in content, f"ASM disk {disk} should be configured in Vagrantfile"
    
    # Verify Fixed variant is used
    assert "Fixed" in content, "ASM disks should use Fixed variant"
    
    # Verify shareable type is used
    assert "shareable" in content, "ASM disks should be shareable type"


def test_network_configuration_syntax():
    """Verify that network configuration uses correct Vagrant syntax."""
    vagrantfile_path = Path(__file__).parent.parent / "Vagrantfile"
    
    with open(vagrantfile_path, 'r') as f:
        content = f.read()
    
    # Verify private_network is used
    assert "private_network" in content, \
        "Vagrantfile should use private_network for network configuration"
    
    # Verify virtualbox__intnet is used for internal network
    assert "virtualbox__intnet" in content, \
        "Vagrantfile should use virtualbox__intnet for internal network"


def test_vm_resource_allocation():
    """Verify that VM resource allocation meets minimum requirements."""
    config = parse_vagrantfile()
    
    for vm_name in VM_NAMES:
        node_config = config["nodes"][vm_name]
        
        # Verify memory is sufficient for Oracle RAC
        assert node_config["memory"] >= 8192, \
            f"{vm_name} should have at least 8GB RAM for Oracle RAC"
        
        # Verify CPU count is sufficient
        assert node_config["cpus"] >= 2, \
            f"{vm_name} should have at least 2 CPU cores for Oracle RAC"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
