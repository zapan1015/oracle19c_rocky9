"""
Property-Based Tests for Security Configuration Validation
Oracle 19c RAC 2-Node Cluster Setup

This module contains property-based tests to verify security configuration
meets all requirements for Oracle RAC (firewall, SELinux, SSH).

Testing Framework: Python Hypothesis
Minimum Iterations: 100 per property
Host Environment: Windows/Linux/Mac (tests execute commands in Linux VMs via vagrant ssh)

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**
"""

import subprocess
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from pathlib import Path
from typing import Dict, Tuple


# ============================================================================
# Test Configuration
# ============================================================================

# Minimum iterations for property-based tests
MIN_ITERATIONS = 100

# VM names
VM_NAMES = ["node1", "node2"]


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


def execute_vm_command(vm_name: str, command: str) -> Tuple[int, str, str]:
    """
    Execute a command inside a VM via vagrant ssh.
    
    Args:
        vm_name: Name of the Vagrant VM (e.g., "node1", "node2")
        command: Shell command to execute
    
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["vagrant", "ssh", vm_name, "-c", command],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def check_firewalld_status(vm_name: str) -> Tuple[bool, bool]:
    """
    Check if firewalld is stopped and disabled on a VM.
    
    Args:
        vm_name: Name of the Vagrant VM
    
    Returns:
        Tuple of (is_stopped, is_disabled)
    """
    # Check if firewalld is active
    returncode, stdout, stderr = execute_vm_command(
        vm_name,
        "systemctl is-active firewalld"
    )
    is_stopped = (stdout != "active")
    
    # Check if firewalld is enabled
    returncode, stdout, stderr = execute_vm_command(
        vm_name,
        "systemctl is-enabled firewalld"
    )
    is_disabled = (stdout != "enabled")
    
    return is_stopped, is_disabled


def check_selinux_mode(vm_name: str) -> Tuple[str, str]:
    """
    Check SELinux mode on a VM (both runtime and persistent).
    
    Args:
        vm_name: Name of the Vagrant VM
    
    Returns:
        Tuple of (runtime_mode, persistent_mode)
    """
    # Check runtime SELinux mode
    returncode, stdout, stderr = execute_vm_command(
        vm_name,
        "getenforce"
    )
    runtime_mode = stdout.lower() if returncode == 0 else "unknown"
    
    # Check persistent SELinux mode from config file
    returncode, stdout, stderr = execute_vm_command(
        vm_name,
        "grep '^SELINUX=' /etc/selinux/config | cut -d= -f2"
    )
    persistent_mode = stdout.lower() if returncode == 0 else "unknown"
    
    return runtime_mode, persistent_mode


def check_ssh_root_login(vm_name: str) -> bool:
    """
    Check if SSH root login is permitted on a VM.
    
    Args:
        vm_name: Name of the Vagrant VM
    
    Returns:
        True if root login is permitted, False otherwise
    """
    # Check PermitRootLogin setting in sshd_config
    returncode, stdout, stderr = execute_vm_command(
        vm_name,
        "grep -E '^PermitRootLogin' /etc/ssh/sshd_config | awk '{print $2}'"
    )
    
    if returncode != 0 or not stdout:
        return False
    
    # PermitRootLogin should be 'yes'
    return stdout.lower() == "yes"


def check_sshd_running(vm_name: str) -> bool:
    """
    Check if sshd service is running on a VM.
    
    Args:
        vm_name: Name of the Vagrant VM
    
    Returns:
        True if sshd is running, False otherwise
    """
    returncode, stdout, stderr = execute_vm_command(
        vm_name,
        "systemctl is-active sshd"
    )
    return stdout == "active"


# ============================================================================
# Property 16: Firewall Disabled Verification
# **Validates: Requirements 6.1**
# ============================================================================

@pytest.mark.property
@settings(
    max_examples=MIN_ITERATIONS,
    deadline=60000,  # 60 seconds per example
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(vm_name=st.sampled_from(VM_NAMES))
def test_property_16_firewall_disabled_verification(vm_name: str):
    """
    **Property 16: 방화벽 비활성화 검증 (Firewall disabled verification)**
    
    Feature: oracle-rac-vagrant-setup, Property 16: 
    For all RAC nodes, firewalld service SHALL be disabled and stopped.
    
    **Validates: Requirements 6.1**
    """
    # Check if VM is running
    status = get_vagrant_status()
    
    if vm_name not in status or status[vm_name] != "running":
        pytest.skip(f"VM {vm_name} is not running. Run 'vagrant up' first.")
    
    # Check firewalld status
    is_stopped, is_disabled = check_firewalld_status(vm_name)
    
    assert is_stopped, \
        f"Firewalld should be stopped on {vm_name}, but it is active"
    
    assert is_disabled, \
        f"Firewalld should be disabled on {vm_name}, but it is enabled"


# ============================================================================
# Property 17: SELinux Permissive Mode Verification
# **Validates: Requirements 6.2, 6.3**
# ============================================================================

@pytest.mark.property
@settings(
    max_examples=MIN_ITERATIONS,
    deadline=60000,  # 60 seconds per example
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(vm_name=st.sampled_from(VM_NAMES))
def test_property_17_selinux_permissive_mode_verification(vm_name: str):
    """
    **Property 17: SELinux Permissive 모드 검증 (SELinux permissive mode verification)**
    
    Feature: oracle-rac-vagrant-setup, Property 17: 
    For all RAC nodes, SELinux SHALL be set to permissive mode and persist after reboot.
    
    **Validates: Requirements 6.2, 6.3**
    """
    # Check if VM is running
    status = get_vagrant_status()
    
    if vm_name not in status or status[vm_name] != "running":
        pytest.skip(f"VM {vm_name} is not running. Run 'vagrant up' first.")
    
    # Check SELinux mode
    runtime_mode, persistent_mode = check_selinux_mode(vm_name)
    
    assert runtime_mode == "permissive", \
        f"SELinux runtime mode should be 'permissive' on {vm_name}, but it is '{runtime_mode}'"
    
    assert persistent_mode == "permissive", \
        f"SELinux persistent mode should be 'permissive' on {vm_name}, but it is '{persistent_mode}'"


# ============================================================================
# Property 18: SSH Root Login Enabled Verification
# **Validates: Requirements 6.4**
# ============================================================================

@pytest.mark.property
@settings(
    max_examples=MIN_ITERATIONS,
    deadline=60000,  # 60 seconds per example
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(vm_name=st.sampled_from(VM_NAMES))
def test_property_18_ssh_root_login_enabled_verification(vm_name: str):
    """
    **Property 18: SSH Root 로그인 허용 검증 (SSH root login enabled verification)**
    
    Feature: oracle-rac-vagrant-setup, Property 18: 
    For all RAC nodes, SSH SHALL be configured to permit root login.
    
    **Validates: Requirements 6.4**
    """
    # Check if VM is running
    status = get_vagrant_status()
    
    if vm_name not in status or status[vm_name] != "running":
        pytest.skip(f"VM {vm_name} is not running. Run 'vagrant up' first.")
    
    # Check if sshd is running
    assert check_sshd_running(vm_name), \
        f"SSH service (sshd) should be running on {vm_name}"
    
    # Check if root login is permitted
    assert check_ssh_root_login(vm_name), \
        f"SSH root login should be permitted on {vm_name}"


# ============================================================================
# Additional Unit Tests for Edge Cases
# ============================================================================

@pytest.mark.unit
def test_firewalld_package_installed():
    """Unit test: Verify firewalld package is installed (even if disabled)"""
    status = get_vagrant_status()
    
    # Find a running VM to test
    running_vm = None
    for vm_name in VM_NAMES:
        if vm_name in status and status[vm_name] == "running":
            running_vm = vm_name
            break
    
    if not running_vm:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    # Check if firewalld package is installed
    returncode, stdout, stderr = execute_vm_command(
        running_vm,
        "rpm -q firewalld"
    )
    
    assert returncode == 0 and "firewalld-" in stdout, \
        f"Firewalld package should be installed on {running_vm}"


@pytest.mark.unit
def test_selinux_config_file_exists():
    """Unit test: Verify SELinux configuration file exists"""
    status = get_vagrant_status()
    
    running_vm = None
    for vm_name in VM_NAMES:
        if vm_name in status and status[vm_name] == "running":
            running_vm = vm_name
            break
    
    if not running_vm:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    # Check if /etc/selinux/config exists
    returncode, stdout, stderr = execute_vm_command(
        running_vm,
        "test -f /etc/selinux/config && echo 'exists'"
    )
    
    assert "exists" in stdout, \
        f"/etc/selinux/config should exist on {running_vm}"


@pytest.mark.unit
def test_sshd_config_file_exists():
    """Unit test: Verify SSH configuration file exists"""
    status = get_vagrant_status()
    
    running_vm = None
    for vm_name in VM_NAMES:
        if vm_name in status and status[vm_name] == "running":
            running_vm = vm_name
            break
    
    if not running_vm:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    # Check if /etc/ssh/sshd_config exists
    returncode, stdout, stderr = execute_vm_command(
        running_vm,
        "test -f /etc/ssh/sshd_config && echo 'exists'"
    )
    
    assert "exists" in stdout, \
        f"/etc/ssh/sshd_config should exist on {running_vm}"


@pytest.mark.unit
def test_firewalld_not_running_on_all_nodes():
    """Unit test: Verify firewalld is not running on any RAC node"""
    status = get_vagrant_status()
    
    running_vms = [vm for vm in VM_NAMES if vm in status and status[vm] == "running"]
    
    if not running_vms:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    for vm_name in running_vms:
        is_stopped, _ = check_firewalld_status(vm_name)
        assert is_stopped, \
            f"Firewalld should not be running on {vm_name}"


@pytest.mark.unit
def test_selinux_permissive_on_all_nodes():
    """Unit test: Verify SELinux is in permissive mode on all RAC nodes"""
    status = get_vagrant_status()
    
    running_vms = [vm for vm in VM_NAMES if vm in status and status[vm] == "running"]
    
    if not running_vms:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    for vm_name in running_vms:
        runtime_mode, _ = check_selinux_mode(vm_name)
        assert runtime_mode == "permissive", \
            f"SELinux should be in permissive mode on {vm_name}, but it is '{runtime_mode}'"


@pytest.mark.unit
def test_ssh_service_enabled_on_all_nodes():
    """Unit test: Verify SSH service is enabled on all RAC nodes"""
    status = get_vagrant_status()
    
    running_vms = [vm for vm in VM_NAMES if vm in status and status[vm] == "running"]
    
    if not running_vms:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    for vm_name in running_vms:
        returncode, stdout, stderr = execute_vm_command(
            vm_name,
            "systemctl is-enabled sshd"
        )
        assert stdout == "enabled", \
            f"SSH service should be enabled on {vm_name}"


@pytest.mark.unit
def test_ssh_password_authentication_enabled():
    """Unit test: Verify SSH password authentication is enabled"""
    status = get_vagrant_status()
    
    running_vm = None
    for vm_name in VM_NAMES:
        if vm_name in status and status[vm_name] == "running":
            running_vm = vm_name
            break
    
    if not running_vm:
        pytest.skip("No VMs are running. Run 'vagrant up' first.")
    
    # Check PasswordAuthentication setting
    returncode, stdout, stderr = execute_vm_command(
        running_vm,
        "grep -E '^PasswordAuthentication' /etc/ssh/sshd_config | awk '{print $2}'"
    )
    
    assert stdout.lower() == "yes", \
        f"SSH password authentication should be enabled on {running_vm}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
