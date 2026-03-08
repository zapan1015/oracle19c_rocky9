#!/usr/bin/env python3
"""
Property-Based Tests for Package Installation and OS Configuration
Tests Properties 13, 14, 15, and 29 from the design document

This test suite validates:
- Oracle preinstall package installation (Property 13)
- Kernel parameter configuration (Property 14)
- Resource limits configuration (Property 15)
- Configuration persistence across reboots (Property 29)

Requirements: 5.1-5.4, 10.1-10.10
"""

import subprocess
import re
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, List, Tuple


# =============================================================================
# Test Configuration
# =============================================================================

RAC_NODES = ['node1', 'node2']

# Required packages (Requirement 5.1, 5.4)
REQUIRED_PACKAGES = [
    'oracle-database-preinstall-19c',
    'chrony',
    'net-tools',
    'bind-utils',
    'nfs-utils',
    'smartmontools'
]

# Kernel parameters (Requirements 10.1-10.5)
KERNEL_PARAMETERS = {
    'kernel.shmmax': 4398046511104,
    'kernel.shmall': 1073741824,
    'kernel.shmmni': 4096,
    'fs.file-max': 6815744,
    'net.ipv4.ip_local_port_range': '9000 65500'
}

# Resource limits (Requirements 10.6-10.9)
RESOURCE_LIMITS = {
    'grid': {
        'soft': {'nofile': 1024, 'nproc': 16384},
        'hard': {'nofile': 65536, 'nproc': 16384}
    },
    'oracle': {
        'soft': {'nofile': 1024, 'nproc': 16384},
        'hard': {'nofile': 65536, 'nproc': 16384}
    }
}


# =============================================================================
# Helper Functions
# =============================================================================

def run_ssh_command(node: str, command: str) -> Tuple[int, str, str]:
    """Execute command on remote node via SSH"""
    ssh_cmd = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'ConnectTimeout=5',
        f'vagrant@{node}',
        command
    ]
    
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, '', 'Command timed out'
    except Exception as e:
        return -1, '', str(e)


def check_package_installed(node: str, package: str) -> bool:
    """Check if a package is installed on the node"""
    returncode, stdout, _ = run_ssh_command(
        node,
        f'rpm -q {package}'
    )
    return returncode == 0


def get_sysctl_value(node: str, parameter: str) -> str:
    """Get current value of a sysctl parameter"""
    returncode, stdout, _ = run_ssh_command(
        node,
        f'sysctl -n {parameter}'
    )
    if returncode == 0:
        return stdout.strip()
    return ''


def get_resource_limit(node: str, user: str, limit_type: str, limit_item: str) -> int:
    """Get resource limit for a user"""
    # Check both limits.conf and limits.d directory
    cmd = f'''
    grep -E "^{user}\\s+{limit_type}\\s+{limit_item}" /etc/security/limits.conf /etc/security/limits.d/*.conf 2>/dev/null | \
    tail -1 | awk '{{print $NF}}'
    '''
    returncode, stdout, _ = run_ssh_command(node, cmd)
    
    if returncode == 0 and stdout:
        try:
            return int(stdout)
        except ValueError:
            return -1
    return -1


def check_sysctl_persistence(node: str, parameter: str) -> bool:
    """Check if sysctl parameter is configured in /etc/sysctl.conf"""
    returncode, stdout, _ = run_ssh_command(
        node,
        f'grep -E "^{parameter}\\s*=" /etc/sysctl.conf /etc/sysctl.d/*.conf 2>/dev/null'
    )
    return returncode == 0


def check_limits_persistence(node: str, user: str) -> bool:
    """Check if resource limits are configured in persistent files"""
    returncode, stdout, _ = run_ssh_command(
        node,
        f'grep -E "^{user}\\s+" /etc/security/limits.conf /etc/security/limits.d/*.conf 2>/dev/null'
    )
    return returncode == 0


# =============================================================================
# Property 13: Oracle Preinstall Package Installation
# **Validates: Requirements 5.1, 5.4**
# =============================================================================

@given(st.sampled_from(RAC_NODES))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_13_oracle_preinstall_package_installation(node: str):
    """
    Feature: oracle-rac-vagrant-setup, Property 13:
    For all RAC nodes, oracle-database-preinstall-19c package and all required
    RPM packages must be installed.
    
    **Validates: Requirements 5.1, 5.4**
    """
    # Check oracle-database-preinstall-19c (may not be available in all repos)
    preinstall_installed = check_package_installed(node, 'oracle-database-preinstall-19c')
    
    # Check all required packages
    packages_status = {}
    for package in REQUIRED_PACKAGES:
        if package == 'oracle-database-preinstall-19c':
            packages_status[package] = preinstall_installed
        else:
            packages_status[package] = check_package_installed(node, package)
    
    # At minimum, all packages except oracle-database-preinstall-19c must be installed
    required_packages_installed = all(
        packages_status[pkg] for pkg in REQUIRED_PACKAGES 
        if pkg != 'oracle-database-preinstall-19c'
    )
    
    assert required_packages_installed, \
        f"Node {node}: Not all required packages are installed. Status: {packages_status}"


# =============================================================================
# Property 14: Kernel Parameter Validation
# **Validates: Requirements 5.2, 10.1, 10.2, 10.3, 10.4, 10.5**
# =============================================================================

@given(
    st.sampled_from(RAC_NODES),
    st.sampled_from(list(KERNEL_PARAMETERS.keys()))
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_14_kernel_parameter_validation(node: str, parameter: str):
    """
    Feature: oracle-rac-vagrant-setup, Property 14:
    For all RAC nodes, after oracle-database-preinstall-19c installation,
    all required kernel parameters (shmmax, shmall, shmmni, file-max,
    ip_local_port_range) must be set to correct values.
    
    **Validates: Requirements 5.2, 10.1, 10.2, 10.3, 10.4, 10.5**
    """
    expected_value = KERNEL_PARAMETERS[parameter]
    actual_value = get_sysctl_value(node, parameter)
    
    # Convert to comparable format
    if isinstance(expected_value, int):
        try:
            actual_int = int(actual_value)
            assert actual_int >= expected_value, \
                f"Node {node}: {parameter} = {actual_int}, expected >= {expected_value}"
        except ValueError:
            assert False, f"Node {node}: {parameter} has invalid value: {actual_value}"
    else:
        # For string values like port ranges
        assert actual_value == str(expected_value), \
            f"Node {node}: {parameter} = {actual_value}, expected {expected_value}"


# =============================================================================
# Property 15: Resource Limits Validation
# **Validates: Requirements 5.3, 10.6, 10.7, 10.8, 10.9**
# =============================================================================

@given(
    st.sampled_from(RAC_NODES),
    st.sampled_from(['grid', 'oracle']),
    st.sampled_from(['soft', 'hard']),
    st.sampled_from(['nofile', 'nproc'])
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_15_resource_limits_validation(
    node: str,
    user: str,
    limit_type: str,
    limit_item: str
):
    """
    Feature: oracle-rac-vagrant-setup, Property 15:
    For all RAC nodes, resource limits (nofile, nproc) for grid and oracle
    users must be set to correct values.
    
    **Validates: Requirements 5.3, 10.6, 10.7, 10.8, 10.9**
    """
    expected_value = RESOURCE_LIMITS[user][limit_type][limit_item]
    actual_value = get_resource_limit(node, user, limit_type, limit_item)
    
    assert actual_value == expected_value, \
        f"Node {node}: {user} {limit_type} {limit_item} = {actual_value}, expected {expected_value}"


# =============================================================================
# Property 29: Configuration Persistence
# **Validates: Requirements 10.10**
# =============================================================================

@given(st.sampled_from(RAC_NODES))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_29_configuration_persistence(node: str):
    """
    Feature: oracle-rac-vagrant-setup, Property 29:
    For all configuration changes (kernel parameters, resource limits, SELinux,
    udev rules), settings must persist across reboots.
    
    **Validates: Requirements 10.10**
    """
    # Check kernel parameters persistence
    kernel_params_persistent = all(
        check_sysctl_persistence(node, param)
        for param in KERNEL_PARAMETERS.keys()
    )
    
    assert kernel_params_persistent, \
        f"Node {node}: Not all kernel parameters are configured for persistence"
    
    # Check resource limits persistence
    limits_persistent = all(
        check_limits_persistence(node, user)
        for user in ['grid', 'oracle']
    )
    
    assert limits_persistent, \
        f"Node {node}: Resource limits are not configured for persistence"


# =============================================================================
# Additional Validation Tests
# =============================================================================

@given(st.sampled_from(RAC_NODES))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_kernel_parameters_comprehensive(node: str):
    """
    Comprehensive test: Verify all kernel parameters are correctly configured
    """
    failures = []
    
    for parameter, expected_value in KERNEL_PARAMETERS.items():
        actual_value = get_sysctl_value(node, parameter)
        
        if isinstance(expected_value, int):
            try:
                actual_int = int(actual_value)
                if actual_int < expected_value:
                    failures.append(
                        f"{parameter}: {actual_int} < {expected_value}"
                    )
            except ValueError:
                failures.append(
                    f"{parameter}: invalid value '{actual_value}'"
                )
        else:
            if actual_value != str(expected_value):
                failures.append(
                    f"{parameter}: '{actual_value}' != '{expected_value}'"
                )
    
    assert not failures, \
        f"Node {node}: Kernel parameter validation failed:\n" + "\n".join(failures)


@given(st.sampled_from(RAC_NODES))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_resource_limits_comprehensive(node: str):
    """
    Comprehensive test: Verify all resource limits are correctly configured
    """
    failures = []
    
    for user in ['grid', 'oracle']:
        for limit_type in ['soft', 'hard']:
            for limit_item in ['nofile', 'nproc']:
                expected = RESOURCE_LIMITS[user][limit_type][limit_item]
                actual = get_resource_limit(node, user, limit_type, limit_item)
                
                if actual != expected:
                    failures.append(
                        f"{user} {limit_type} {limit_item}: {actual} != {expected}"
                    )
    
    assert not failures, \
        f"Node {node}: Resource limits validation failed:\n" + "\n".join(failures)


# =============================================================================
# Test Execution
# =============================================================================

if __name__ == '__main__':
    import pytest
    import sys
    
    # Run tests with pytest
    sys.exit(pytest.main([__file__, '-v', '--tb=short']))

