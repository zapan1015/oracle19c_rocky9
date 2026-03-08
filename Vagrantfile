# -*- mode: ruby -*-
# vi: set ft=ruby :

# Oracle 19c RAC 2-Node Cluster Vagrant Configuration
# Requirements: VirtualBox, Vagrant
# Base Image: rockylinux/9

Vagrant.configure("2") do |config|
  # Base box configuration
  config.vm.box = "rockylinux/9"
  
  # Disable automatic box update checking
  config.vm.box_check_update = false
  
  # Synced folder configuration - exclude large disk files
  config.vm.synced_folder ".", "/vagrant",
    type: "rsync",
    rsync__exclude: [".git/", ".vagrant/", "asm_disk1.vdi", "asm_disk2.vdi", "asm_disk3.vdi", "*.vdi", "*.vmdk", "*.vbox"]
  
  # ============================================================================
  # Node 1 Configuration
  # ============================================================================
  config.vm.define "node1" do |node1|
    # Hostname configuration
    node1.vm.hostname = "node1.localdomain"
    
    # Provisioning: Configure /etc/hosts
    node1.vm.provision "shell", path: "scripts/setup_hosts.sh"
    
    # Network configuration
    # Adapter 1: Public Network (private_network type) - 192.168.1.0/24
    node1.vm.network "private_network", ip: "192.168.1.101"
    
    # Adapter 2: Private Network (virtualbox__intnet) - 10.0.0.0/24
    # Used for RAC interconnect (Cache Fusion)
    node1.vm.network "private_network", 
                     ip: "10.0.0.101",
                     virtualbox__intnet: "rac-private"
    
    # VirtualBox provider configuration
    node1.vm.provider "virtualbox" do |vb|
      # VM name in VirtualBox
      vb.name = "rac-node1"
      
      # Resource allocation
      vb.memory = "8192"  # 8GB RAM
      vb.cpus = 2         # 2 CPU cores
      
      # Enable GUI for troubleshooting (optional)
      vb.gui = false
      
      # Additional VirtualBox settings for Oracle RAC
      vb.customize ["modifyvm", :id, "--groups", "/Oracle RAC"]
      vb.customize ["modifyvm", :id, "--description", "Oracle 19c RAC Node 1"]
      
      # ========================================================================
      # Shared Storage Configuration for ASM
      # ========================================================================
      # Create shared disks if they don't exist (idempotent)
      # All disks use Fixed variant for performance and Shareable type for multi-VM access
      
      # ASM Disk 1 - 20GB for DATA disk group
      unless File.exist?("asm_disk1.vdi")
        vb.customize ['createmedium', 'disk', 
                      '--filename', 'asm_disk1.vdi',
                      '--size', 20480,  # 20GB in MB
                      '--format', 'VDI',
                      '--variant', 'Fixed']
      end
      
      # ASM Disk 2 - 20GB for DATA disk group
      unless File.exist?("asm_disk2.vdi")
        vb.customize ['createmedium', 'disk',
                      '--filename', 'asm_disk2.vdi',
                      '--size', 20480,  # 20GB in MB
                      '--format', 'VDI',
                      '--variant', 'Fixed']
      end
      
      # ASM Disk 3 - 10GB for FRA (Fast Recovery Area) disk group
      unless File.exist?("asm_disk3.vdi")
        vb.customize ['createmedium', 'disk',
                      '--filename', 'asm_disk3.vdi',
                      '--size', 10240,  # 10GB in MB
                      '--format', 'VDI',
                      '--variant', 'Fixed']
      end
      
      # Attach shared disks to node1 via SATA Controller
      # Port numbers: 1, 2, 3 (port 0 is typically used by OS disk)
      # mtype: shareable - allows multiple VMs to access the same disk
      vb.customize ['storageattach', :id,
                    '--storagectl', 'SATA Controller',
                    '--port', 1,
                    '--device', 0,
                    '--type', 'hdd',
                    '--medium', 'asm_disk1.vdi',
                    '--mtype', 'shareable']
      
      vb.customize ['storageattach', :id,
                    '--storagectl', 'SATA Controller',
                    '--port', 2,
                    '--device', 0,
                    '--type', 'hdd',
                    '--medium', 'asm_disk2.vdi',
                    '--mtype', 'shareable']
      
      vb.customize ['storageattach', :id,
                    '--storagectl', 'SATA Controller',
                    '--port', 3,
                    '--device', 0,
                    '--type', 'hdd',
                    '--medium', 'asm_disk3.vdi',
                    '--mtype', 'shareable']
    end
  end
  
  # ============================================================================
  # Node 2 Configuration
  # ============================================================================
  config.vm.define "node2" do |node2|
    # Hostname configuration
    node2.vm.hostname = "node2.localdomain"
    
    # Provisioning: Configure /etc/hosts (runs first)
    node2.vm.provision "shell", path: "scripts/setup_hosts.sh"
    
    # Provisioning: Setup DNS with dnsmasq (runs second)
    node2.vm.provision "shell", path: "scripts/setup_dnsmasq.sh"
    
    # Provisioning: Install Ansible and prepare environment (runs third)
    node2.vm.provision "shell", inline: <<-SHELL
      # Install EPEL repository
      if ! rpm -q epel-release &> /dev/null; then
        echo "Installing EPEL repository..."
        dnf install -y epel-release
      fi
      
      # Install Ansible if not already installed
      if ! command -v ansible &> /dev/null; then
        echo "Installing Ansible..."
        dnf install -y ansible-core
      fi
      
      # Install sshpass for SSH key distribution
      if ! command -v sshpass &> /dev/null; then
        echo "Installing sshpass..."
        dnf install -y sshpass
      fi
      
      # Generate SSH key for root if not exists
      if [ ! -f /root/.ssh/id_rsa ]; then
        echo "Generating SSH key for root..."
        ssh-keygen -t rsa -b 2048 -f /root/.ssh/id_rsa -N ""
      fi
      
      # Wait for node1 to be ready
      echo "Waiting for node1 to be ready..."
      for i in {1..30}; do
        if ping -c 1 192.168.1.101 &> /dev/null; then
          echo "node1 is reachable"
          break
        fi
        sleep 2
      done
      
      # Enable root SSH access on both nodes
      echo "Enabling root SSH access..."
      sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
      sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
      systemctl restart sshd
      
      # Set root password temporarily for SSH key distribution
      echo "root:vagrant" | chpasswd
      
      # Copy SSH key to node1 via vagrant user and then to root
      echo "Setting up SSH key-based authentication to node1..."
      su - vagrant -c "ssh -o StrictHostKeyChecking=no vagrant@192.168.1.101 'echo vagrant | sudo -S bash -c \"
        sed -i \\\"s/^#PermitRootLogin.*/PermitRootLogin yes/\\\" /etc/ssh/sshd_config
        sed -i \\\"s/^PermitRootLogin.*/PermitRootLogin yes/\\\" /etc/ssh/sshd_config
        systemctl restart sshd
        echo root:vagrant | chpasswd
      \"'" 2>/dev/null || true
      
      sleep 2
      
      # Now copy SSH key to root@node1
      sshpass -p 'vagrant' ssh-copy-id -o StrictHostKeyChecking=no root@192.168.1.101 2>/dev/null || true
      
      # Copy SSH key to localhost (node2 itself)
      cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
      chmod 600 /root/.ssh/authorized_keys
      
      # Test SSH connection
      echo "Testing SSH connection to node1..."
      ssh -o StrictHostKeyChecking=no root@192.168.1.101 'echo "SSH connection successful"' || echo "SSH connection failed"
      
      echo "Ansible environment prepared successfully"
    SHELL
    
    # Provisioning: Run Ansible playbook (runs last)
    node2.vm.provision "ansible_local" do |ansible|
      ansible.playbook = "/vagrant/ansible/site.yml"
      ansible.inventory_path = "/vagrant/ansible/hosts.ini"
      ansible.limit = "all"
      ansible.verbose = true
      ansible.install = false  # Already installed in previous step
    end
    
    # Network configuration
    # Adapter 1: Public Network (private_network type) - 192.168.1.0/24
    node2.vm.network "private_network", ip: "192.168.1.102"
    
    # Adapter 2: Private Network (virtualbox__intnet) - 10.0.0.0/24
    # Used for RAC interconnect (Cache Fusion)
    node2.vm.network "private_network",
                     ip: "10.0.0.102",
                     virtualbox__intnet: "rac-private"
    
    # VirtualBox provider configuration
    node2.vm.provider "virtualbox" do |vb|
      # VM name in VirtualBox
      vb.name = "rac-node2"
      
      # Resource allocation
      vb.memory = "8192"  # 8GB RAM
      vb.cpus = 2         # 2 CPU cores
      
      # Enable GUI for troubleshooting (optional)
      vb.gui = false
      
      # Additional VirtualBox settings for Oracle RAC
      vb.customize ["modifyvm", :id, "--groups", "/Oracle RAC"]
      vb.customize ["modifyvm", :id, "--description", "Oracle 19c RAC Node 2"]
      
      # ========================================================================
      # Attach Shared Storage to node2
      # ========================================================================
      # Attach the same shared disks created for node1
      # These disks are already created and configured as shareable
      
      vb.customize ['storageattach', :id,
                    '--storagectl', 'SATA Controller',
                    '--port', 1,
                    '--device', 0,
                    '--type', 'hdd',
                    '--medium', 'asm_disk1.vdi',
                    '--mtype', 'shareable']
      
      vb.customize ['storageattach', :id,
                    '--storagectl', 'SATA Controller',
                    '--port', 2,
                    '--device', 0,
                    '--type', 'hdd',
                    '--medium', 'asm_disk2.vdi',
                    '--mtype', 'shareable']
      
      vb.customize ['storageattach', :id,
                    '--storagectl', 'SATA Controller',
                    '--port', 3,
                    '--device', 0,
                    '--type', 'hdd',
                    '--medium', 'asm_disk3.vdi',
                    '--mtype', 'shareable']
    end
  end
end
