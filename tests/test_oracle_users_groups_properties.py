"""
Property-Based Tests for Oracle Users, Groups, and Directories Configuration
Tests Properties 10, 11, and 12 from the design document

These tests validate that Oracle groups, users, and directories are correctly
configured on all RAC nodes with proper UIDs, GIDs, ownership, and permissions.

**Validates: Requirements 4.1-4.13**
"""

import subprocess
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import yaml
import os


# =============================================================================
# Test Configuration and Helpers
# =============================================================================

def load_ansible_vars():
    """Load Oracle configuration from Ansible group_vars"""
    vars_file = os.path.join(os.path.dirname(__file__), '..', 'ansible', 'group_vars', 'rac_nodes.yml')
    with open(vars_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_rac_nodes():
    """Get list of RAC nodes from Ansible inventory"""
    return ['node1', 'node2']


def run_vagrant_ssh_command(node, command):
    """Execute command on a node via vagrant ssh"""
    try:
        result = subprocess.run(
            ['vagrant', 'ssh', node, '-c', command],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, '', 'Command timed out'
    except Exception as e:
        return -1, '', str(e)


def check_group_exists(node, group_name, expected_gid):
    """Check if a group exists with the correct GID on a node"""
    returncode, stdout, stderr = run_vagrant_ssh_command(
        node,
        f"getent group {group_name}"
    )
    
    if returncode != 0:
        return False, f"Group {group_name} not found on {node}"
    
    # Parse output: groupname:x:gid:members
    parts = stdout.split(':')
    if len(parts) < 3:
        return False, f"Invalid group entry format on {node}"
    
    actual_gid = int(parts[2])
    if actual_gid != expected_gid:
        return False, f"Group {group_name} has GID {actual_gid}, expected {expected_gid} on {node}"
    
    return True, f"Group {group_name} exists with correct GID {expected_gid} on {node}"


def check_user_exists(node, user_name, expected_uid, expected_primary_group, expected_secondary_groups):
    """Check if a user exists with correct UID and group memberships on a node"""
    # Check user exists and has correct UID
    returncode, stdout, stderr = run_vagrant_ssh_command(
        node,
        f"getent passwd {user_name}"
    )
    
    if returncode != 0:
        return False, f"User {user_name} not found on {node}"
    
    # Parse output: username:x:uid:gid:comment:home:shell
    parts = stdout.split(':')
    if len(parts) < 4:
        return False, f"Invalid user entry format on {node}"
    
    actual_uid = int(parts[2])
    if actual_uid != expected_uid:
        return False, f"User {user_name} has UID {actual_uid}, expected {expected_uid} on {node}"
    
    # Check primary group
    returncode, stdout, stderr = run_vagrant_ssh_command(
        node,
        f"id -gn {user_name}"
    )
    
    if returncode != 0:
        return False, f"Cannot get primary group for {user_name} on {node}"
    
    actual_primary_group = stdout.strip()
    if actual_primary_group != expected_primary_group:
        return False, f"User {user_name} has primary group {actual_primary_group}, expected {expected_primary_group} on {node}"
    
    # Check secondary groups
    returncode, stdout, stderr = run_vagrant_ssh_command(
        node,
        f"id -Gn {user_name}"
    )
    
    if returncode != 0:
        return False, f"Cannot get groups for {user_name} on {node}"
    
    actual_groups = set(stdout.strip().split())
    expected_groups = set([expected_primary_group] + expected_secondary_groups)
    
    if not expected_groups.issubset(actual_groups):
        missing_groups = expected_groups - actual_groups
        return False, f"User {user_name} missing groups {missing_groups} on {node}"
    
    return True, f"User {user_name} exists with correct UID {expected_uid} and groups on {node}"


def check_directory_exists(node, path, expected_owner, expected_group, expected_mode):
    """Check if a directory exists with correct ownership and permissions on a node"""
    # Check directory exists
    returncode, stdout, stderr = run_vagrant_ssh_command(
        node,
        f"test -d {path} && echo 'exists' || echo 'not_found'"
    )
    
    if returncode != 0 or stdout != 'exists':
        return False, f"Directory {path} not found on {node}"
    
    # Check ownership
    returncode, stdout, stderr = run_vagrant_ssh_command(
        node,
        f"stat -c '%U:%G' {path}"
    )
    
    if returncode != 0:
        return False, f"Cannot get ownership for {path} on {node}"
    
    actual_owner, actual_group = stdout.split(':')
    if actual_owner != expected_owner or actual_group != expected_group:
        return False, f"Directory {path} has ownership {actual_owner}:{actual_group}, expected {expected_owner}:{expected_group} on {node}"
    
    # Check permissions (mode)
    returncode, stdout, stderr = run_vagrant_ssh_command(
        node,
        f"stat -c '%a' {path}"
    )
    
    if returncode != 0:
        return False, f"Cannot get permissions for {path} on {node}"
    
    actual_mode = stdout.strip()
    # Remove leading '0' from expected_mode if present (e.g., '0755' -> '755')
    expected_mode_str = expected_mode.lstrip('0')
    
    if actual_mode != expected_mode_str:
        return False, f"Directory {path} has permissions {actual_mode}, expected {expected_mode_str} on {node}"
    
    return True, f"Directory {path} exists with correct ownership and permissions on {node}"


# =============================================================================
# Property 10: Oracle Groups Configuration
# **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
# =============================================================================

@pytest.mark.property
@settings(
    max_examples=100,
    deadline=60000,  # 60 seconds per example
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(node_index=st.integers(min_value=0, max_value=1))
def test_property_10_oracle_groups_configuration(node_index):
    """
    **Property 10: Oracle Groups Configuration**
    
    For all RAC nodes, the following groups must exist with specified GIDs:
    - oinstall (54321)
    - dba (54322)
    - asmdba (54327)
    - asmoper (54328)
    - asmadmin (54329)
    
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    """
    # Load configuration
    config = load_ansible_vars()
    nodes = get_rac_nodes()
    node = nodes[node_index]
    
    # Get expected groups from configuration
    expected_groups = config['oracle_groups']
    
    # Verify each group exists with correct GID
    for group in expected_groups:
        success, message = check_group_exists(node, group['name'], group['gid'])
        assert success, message


# =============================================================================
# Property 11: Oracle Users Configuration
# **Validates: Requirements 4.6, 4.7, 4.8, 4.9**
# =============================================================================

@pytest.mark.property
@settings(
    max_examples=100,
    deadline=60000,  # 60 seconds per example
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(node_index=st.integers(min_value=0, max_value=1))
def test_property_11_oracle_users_configuration(node_index):
    """
    **Property 11: Oracle Users Configuration**
    
    For all RAC nodes, grid user (UID 54331) and oracle user (UID 54321) 
    must exist with primary group oinstall and correct secondary groups:
    - grid: asmadmin, asmdba, asmoper
    - oracle: dba, asmdba, asmadmin
    
    **Validates: Requirements 4.6, 4.7, 4.8, 4.9**
    """
    # Load configuration
    config = load_ansible_vars()
    nodes = get_rac_nodes()
    node = nodes[node_index]
    
    # Get expected users from configuration
    expected_users = config['oracle_users']
    
    # Verify each user exists with correct UID and groups
    for user in expected_users:
        success, message = check_user_exists(
            node,
            user['name'],
            user['uid'],
            user['primary_group'],
            user['secondary_groups']
        )
        assert success, message


# =============================================================================
# Property 12: Oracle Directory Structure
# **Validates: Requirements 4.10, 4.11, 4.12, 4.13**
# =============================================================================

@pytest.mark.property
@settings(
    max_examples=100,
    deadline=60000,  # 60 seconds per example
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(node_index=st.integers(min_value=0, max_value=1))
def test_property_12_oracle_directory_structure(node_index):
    """
    **Property 12: Oracle Directory Structure**
    
    For all RAC nodes, the following directories must exist with correct ownership:
    - /u01/app/grid (owner: grid, group: oinstall)
    - /u01/app/19.3.0/grid (owner: grid, group: oinstall)
    - /u01/app/oracle (owner: oracle, group: oinstall)
    - /u01/app/oracle/product/19.3.0/dbhome_1 (owner: oracle, group: oinstall)
    
    **Validates: Requirements 4.10, 4.11, 4.12, 4.13**
    """
    # Load configuration
    config = load_ansible_vars()
    nodes = get_rac_nodes()
    node = nodes[node_index]
    
    # Get expected directories from configuration
    expected_directories = config['oracle_directories']
    
    # Verify each directory exists with correct ownership and permissions
    for directory in expected_directories:
        success, message = check_directory_exists(
            node,
            directory['path'],
            directory['owner'],
            directory['group'],
            directory['mode']
        )
        assert success, message


# =============================================================================
# Additional Unit Tests for Specific Edge Cases
# =============================================================================

@pytest.mark.unit
def test_all_required_groups_defined_in_config():
    """Unit test: Verify all required Oracle groups are defined in configuration"""
    config = load_ansible_vars()
    groups = config['oracle_groups']
    group_names = [g['name'] for g in groups]
    
    required_groups = ['oinstall', 'dba', 'asmdba', 'asmoper', 'asmadmin']
    for required_group in required_groups:
        assert required_group in group_names, f"Required group {required_group} not found in configuration"


@pytest.mark.unit
def test_all_required_users_defined_in_config():
    """Unit test: Verify all required Oracle users are defined in configuration"""
    config = load_ansible_vars()
    users = config['oracle_users']
    user_names = [u['name'] for u in users]
    
    required_users = ['grid', 'oracle']
    for required_user in required_users:
        assert required_user in user_names, f"Required user {required_user} not found in configuration"


@pytest.mark.unit
def test_all_required_directories_defined_in_config():
    """Unit test: Verify all required Oracle directories are defined in configuration"""
    config = load_ansible_vars()
    directories = config['oracle_directories']
    directory_paths = [d['path'] for d in directories]
    
    required_directories = [
        '/u01/app/grid',
        '/u01/app/19.3.0/grid',
        '/u01/app/oracle',
        '/u01/app/oracle/product/19.3.0/dbhome_1'
    ]
    for required_dir in required_directories:
        assert required_dir in directory_paths, f"Required directory {required_dir} not found in configuration"


@pytest.mark.unit
def test_grid_user_has_correct_secondary_groups():
    """Unit test: Verify grid user has correct secondary groups"""
    config = load_ansible_vars()
    users = config['oracle_users']
    
    grid_user = next((u for u in users if u['name'] == 'grid'), None)
    assert grid_user is not None, "Grid user not found in configuration"
    
    expected_groups = {'asmadmin', 'asmdba', 'asmoper'}
    actual_groups = set(grid_user['secondary_groups'])
    
    assert expected_groups == actual_groups, f"Grid user has incorrect secondary groups: {actual_groups}, expected {expected_groups}"


@pytest.mark.unit
def test_oracle_user_has_correct_secondary_groups():
    """Unit test: Verify oracle user has correct secondary groups"""
    config = load_ansible_vars()
    users = config['oracle_users']
    
    oracle_user = next((u for u in users if u['name'] == 'oracle'), None)
    assert oracle_user is not None, "Oracle user not found in configuration"
    
    expected_groups = {'dba', 'asmdba', 'asmadmin'}
    actual_groups = set(oracle_user['secondary_groups'])
    
    assert expected_groups == actual_groups, f"Oracle user has incorrect secondary groups: {actual_groups}, expected {expected_groups}"


@pytest.mark.unit
def test_grid_directories_have_grid_owner():
    """Unit test: Verify Grid Infrastructure directories have grid as owner"""
    config = load_ansible_vars()
    directories = config['oracle_directories']
    
    grid_directories = [d for d in directories if 'grid' in d['path']]
    
    for directory in grid_directories:
        assert directory['owner'] == 'grid', f"Grid directory {directory['path']} should have owner 'grid', not '{directory['owner']}'"


@pytest.mark.unit
def test_oracle_directories_have_oracle_owner():
    """Unit test: Verify Oracle Database directories have oracle as owner"""
    config = load_ansible_vars()
    directories = config['oracle_directories']
    
    oracle_directories = [d for d in directories if 'oracle' in d['path'] and 'grid' not in d['path']]
    
    for directory in oracle_directories:
        assert directory['owner'] == 'oracle', f"Oracle directory {directory['path']} should have owner 'oracle', not '{directory['owner']}'"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
