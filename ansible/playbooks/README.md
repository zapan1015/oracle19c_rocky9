# Ansible Playbooks for Oracle RAC Setup

This directory contains Ansible playbooks for configuring Oracle RAC nodes.

## Playbooks

### 01_oracle_users_groups.yml

Configures Oracle users, groups, and directory structure on all RAC nodes.

**Requirements Covered:** 4.1-4.13

**What it does:**
- Creates Oracle groups (oinstall, dba, asmdba, asmoper, asmadmin) with specified GIDs
- Creates Oracle users (grid, oracle) with specified UIDs and group memberships
- Creates Oracle directory structure with correct ownership and permissions
- Verifies all configurations

**Usage:**

```bash
# Run from node2 (Ansible control node)
ansible-playbook -i ../hosts.ini 01_oracle_users_groups.yml

# Run with verbose output
ansible-playbook -i ../hosts.ini 01_oracle_users_groups.yml -v

# Run only specific tags
ansible-playbook -i ../hosts.ini 01_oracle_users_groups.yml --tags oracle_groups
ansible-playbook -i ../hosts.ini 01_oracle_users_groups.yml --tags oracle_users
ansible-playbook -i ../hosts.ini 01_oracle_users_groups.yml --tags oracle_directories
ansible-playbook -i ../hosts.ini 01_oracle_users_groups.yml --tags verify

# Dry run (check mode)
ansible-playbook -i ../hosts.ini 01_oracle_users_groups.yml --check
```

**Variables:**

All variables are defined in `ansible/group_vars/rac_nodes.yml`:
- `oracle_groups`: List of Oracle groups with GIDs
- `oracle_users`: List of Oracle users with UIDs and group memberships
- `oracle_directories`: List of Oracle directories with ownership and permissions

**Idempotency:**

This playbook is idempotent and can be run multiple times safely. It will only make changes if the current state differs from the desired state.

## Testing

Property-based tests are available in `tests/test_oracle_users_groups_properties.py`.

**Run tests:**

```bash
# From project root
cd tests
pytest test_oracle_users_groups_properties.py -v

# Run only property tests
pytest test_oracle_users_groups_properties.py -v -m property

# Run only unit tests
pytest test_oracle_users_groups_properties.py -v -m unit

# Run with Hypothesis statistics
pytest test_oracle_users_groups_properties.py -v --hypothesis-show-statistics
```

**Test Coverage:**
- Property 10: Oracle groups configuration (Requirements 4.1-4.5)
- Property 11: Oracle users configuration (Requirements 4.6-4.9)
- Property 12: Oracle directory structure (Requirements 4.10-4.13)

## Verification

After running the playbook, verify the configuration:

```bash
# Check groups on node1
vagrant ssh node1 -c "getent group oinstall dba asmdba asmoper asmadmin"

# Check users on node1
vagrant ssh node1 -c "id grid"
vagrant ssh node1 -c "id oracle"

# Check directories on node1
vagrant ssh node1 -c "ls -la /u01/app/"

# Check groups on node2
vagrant ssh node2 -c "getent group oinstall dba asmdba asmoper asmadmin"

# Check users on node2
vagrant ssh node2 -c "id grid"
vagrant ssh node2 -c "id oracle"

# Check directories on node2
vagrant ssh node2 -c "ls -la /u01/app/"
```

## Troubleshooting

**Issue: Groups already exist with different GIDs**

If groups already exist with different GIDs, you'll need to:
1. Remove the existing groups
2. Re-run the playbook

```bash
# On each node
sudo groupdel oinstall
sudo groupdel dba
# ... etc
```

**Issue: Users already exist with different UIDs**

If users already exist with different UIDs, you'll need to:
1. Remove the existing users
2. Re-run the playbook

```bash
# On each node
sudo userdel -r grid
sudo userdel -r oracle
```

**Issue: Directories already exist with wrong ownership**

The playbook will fix ownership automatically. Just re-run it.

**Issue: Ansible connection fails**

Ensure:
1. VMs are running: `vagrant status`
2. SSH is configured: `vagrant ssh-config`
3. Ansible inventory is correct: `ansible -i hosts.ini rac_nodes -m ping`

## Next Steps

After successfully running this playbook:
1. Run package installation playbook (06_packages_os_config.yml)
2. Run security configuration playbook (08_security_config.yml)
3. Run SSH user equivalence playbook (09_ssh_user_equivalence.yml)
4. Continue with remaining playbooks in sequence
