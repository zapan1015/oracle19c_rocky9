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
    
    # Provisioning: Configure /etc/hosts
    node2.vm.provision "shell", path: "scripts/setup_hosts.sh"
    
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
