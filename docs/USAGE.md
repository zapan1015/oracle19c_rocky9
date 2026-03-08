# Oracle RAC Vagrant Setup - 사용 가이드

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [설치 및 실행](#설치-및-실행)
3. [검증 방법](#검증-방법)
4. [일반적인 작업](#일반적인-작업)
5. [성능 최적화](#성능-최적화)
6. [백업 및 복구](#백업-및-복구)

## 시스템 요구사항

### 하드웨어 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| CPU | 4코어 (가상화 지원) | 8코어 이상 |
| RAM | 20GB | 32GB 이상 |
| 디스크 | 100GB 여유 공간 | 200GB 이상 SSD |
| 네트워크 | 1Gbps | 1Gbps 이상 |

### 소프트웨어 요구사항

#### 필수 소프트웨어

1. **VirtualBox 6.1+**
   - 다운로드: https://www.virtualbox.org/wiki/Downloads
   - 설치 후 확인: `VBoxManage --version`

2. **Vagrant 2.2+**
   - 다운로드: https://www.vagrantup.com/downloads
   - 설치 후 확인: `vagrant --version`

3. **Git**
   - Windows: https://git-scm.com/download/win
   - macOS: `brew install git`
   - Linux: `sudo apt-get install git` 또는 `sudo yum install git`

#### 선택 소프트웨어

1. **Python 3.8+** (테스트 실행용)
   - 다운로드: https://www.python.org/downloads/
   - 설치 후 확인: `python --version`

2. **pytest** (Property-Based 테스트용)
   - 설치: `pip install -r tests/requirements.txt`

### OS별 설정

#### Windows

1. **가상화 활성화**
   - BIOS에서 Intel VT-x 또는 AMD-V 활성화
   - Hyper-V 비활성화 (VirtualBox와 충돌)
   
2. **방화벽 설정**
   - VirtualBox 네트워크 어댑터 허용

#### macOS

1. **가상화 활성화**
   - 최신 macOS는 기본적으로 활성화됨
   
2. **보안 설정**
   - 시스템 환경설정 > 보안 및 개인 정보 보호 > VirtualBox 허용

#### Linux

1. **가상화 활성화**
   - 확인: `egrep -c '(vmx|svm)' /proc/cpuinfo` (0보다 큰 값)
   
2. **사용자 권한**
   - VirtualBox 그룹에 사용자 추가: `sudo usermod -aG vboxusers $USER`

## 설치 및 실행

### 1단계: 프로젝트 클론

```bash
# HTTPS로 클론
git clone https://github.com/zapan1015/oracle19c_rocky9.git
cd oracle19c_rocky9

# 또는 SSH로 클론
git clone git@github.com:zapan1015/oracle19c_rocky9.git
cd oracle19c_rocky9
```

### 2단계: 실행 전 확인

```bash
# 1. VirtualBox 버전 확인
VBoxManage --version
# 예상 출력: 7.0.x

# 2. Vagrant 버전 확인
vagrant --version
# 예상 출력: Vagrant 2.3.x

# 3. 디스크 공간 확인
# Windows
wmic logicaldisk get size,freespace,caption

# Linux/Mac
df -h .

# 4. 메모리 확인
# Windows
systeminfo | findstr /C:"Total Physical Memory"

# Linux
free -h

# Mac
sysctl hw.memsize
```

### 3단계: VM 프로비저닝 시작

```bash
# 전체 프로세스 시작
vagrant up

# 예상 소요 시간: 15-25분
# - VM 생성: 5-10분
# - Ansible 구성: 10-15분
```

### 실행 단계별 설명

#### Phase 1: VM 생성 (5-10분)

```
==> node1: Importing base box 'rockylinux/9'...
==> node1: Matching MAC address for NAT networking...
==> node1: Setting the name of the VM: rac-node1
==> node1: Clearing any previously set network interfaces...
==> node1: Preparing network interfaces based on configuration...
==> node1: Forwarding ports...
==> node1: Running 'pre-boot' VM customizations...
==> node1: Booting VM...
==> node1: Waiting for machine to boot...
```

**이 단계에서 수행되는 작업**:
- Rocky Linux 9 베이스 이미지 다운로드 (처음 한 번만)
- VM 생성 및 리소스 할당 (8GB RAM, 2 CPU)
- 네트워크 어댑터 구성 (Public + Private)
- 공유 스토리지 생성 및 연결 (ASM 디스크)

#### Phase 2: Shell Provisioner (2-3분)

```
==> node1: Running provisioner: shell (setup_hosts.sh)...
==> node2: Running provisioner: shell (setup_hosts.sh)...
==> node2: Running provisioner: shell (setup_dnsmasq.sh)...
```

**이 단계에서 수행되는 작업**:
- /etc/hosts 파일 구성 (모든 노드)
- dnsmasq 설치 및 구성 (node2만)
- DNS 서비스 시작

#### Phase 3: Ansible 환경 준비 (1-2분)

```
==> node2: Running provisioner: shell (ansible setup)...
    node2: Installing EPEL repository...
    node2: Installing Ansible...
    node2: Installing sshpass...
    node2: Generating SSH key for root...
    node2: Setting up SSH key-based authentication to node1...
```

**이 단계에서 수행되는 작업**:
- Ansible 설치
- SSH 키 생성 및 배포
- node2를 Ansible control node로 설정

#### Phase 4: Ansible 구성 (10-15분)

```
==> node2: Running provisioner: ansible_local (site.yml)...
    node2: Running ansible-playbook...
    
PLAY [Configure Oracle RAC Nodes] **********************************************

TASK [Include Oracle users and groups playbook] ********************************
ok: [node1]
ok: [node2]

TASK [Include package installation and OS configuration playbook] **************
changed: [node1]
changed: [node2]

TASK [Include security configuration playbook] *********************************
changed: [node1]
changed: [node2]

TASK [Include SSH User Equivalence playbook] ***********************************
changed: [node1]
changed: [node2]

TASK [Include time synchronization playbook] ***********************************
changed: [node1]
changed: [node2]

TASK [Include shared storage configuration playbook] ***************************
changed: [node1]
changed: [node2]

TASK [Include systemd and cgroup configuration playbook] ***********************
changed: [node1]
changed: [node2]

PLAY RECAP *********************************************************************
node1                      : ok=XX   changed=XX   unreachable=0    failed=0
node2                      : ok=XX   changed=XX   unreachable=0    failed=0
```

**이 단계에서 수행되는 작업**:
1. Oracle 사용자 및 그룹 생성
2. Oracle Preinstall 패키지 설치
3. 커널 매개변수 및 리소스 제한 설정
4. 보안 구성 (방화벽, SELinux, SSH)
5. SSH User Equivalence 설정
6. 시간 동기화 (chrony)
7. 공유 스토리지 구성 (udev rules)
8. Systemd 및 Cgroup v2 구성

### 4단계: 완료 확인

```bash
# VM 상태 확인
vagrant status

# 예상 출력:
# Current machine states:
# 
# node1                     running (virtualbox)
# node2                     running (virtualbox)
```

## 검증 방법

### Python 기반 Property 테스트

```bash
# 1. Python 패키지 설치 (처음 한 번만)
pip install -r tests/requirements.txt

# 2. 모든 테스트 실행 (100회 반복)
pytest tests/ -v

# 3. 특정 테스트만 실행
pytest tests/test_vagrantfile_properties.py -v
pytest tests/test_dns_properties.py -v
pytest tests/test_oracle_users_groups_properties.py -v
pytest tests/test_packages_os_config_properties.py -v

# 4. 특정 Property만 테스트
pytest tests/test_vagrantfile_properties.py::test_property_1_vm_configuration_consistency -v
```

### Bash 검증 스크립트

```bash
# 모든 검증 스크립트 실행
vagrant ssh node2 -c "bash /vagrant/tests/verify_all.sh"

# 개별 검증
vagrant ssh node2 -c "bash /vagrant/tests/verify_network.sh"
vagrant ssh node2 -c "bash /vagrant/tests/verify_dns.sh"
vagrant ssh node2 -c "bash /vagrant/tests/verify_ssh.sh"
vagrant ssh node2 -c "bash /vagrant/tests/verify_storage.sh"
vagrant ssh node2 -c "bash /vagrant/tests/verify_system.sh"
```

### 수동 검증

```bash
# 1. VM 접속
vagrant ssh node1

# 2. Oracle 사용자 확인
id grid
id oracle

# 3. 네트워크 연결 확인
ping -c 3 192.168.1.102
ping -c 3 10.0.0.102

# 4. DNS 확인
nslookup rac-scan.localdomain 192.168.1.102

# 5. SSH User Equivalence 확인
sudo su - grid
ssh node2 hostname
ssh node1 hostname

# 6. 공유 스토리지 확인
ls -l /dev/sd[bcd]

# 7. 커널 매개변수 확인
sysctl kernel.shmmax
sysctl kernel.shmall

# 8. Systemd 설정 확인
systemctl show-environment
```

## 일반적인 작업

### VM 관리

```bash
# VM 중지
vagrant halt

# VM 재시작
vagrant reload

# VM 삭제 (데이터 삭제)
vagrant destroy

# 특정 VM만 관리
vagrant halt node1
vagrant up node1
vagrant destroy node2 -f
```

### 구성 재적용

```bash
# 전체 재프로비저닝
vagrant provision

# 특정 VM만 재프로비저닝
vagrant provision node2

# Ansible만 재실행 (node2에서)
vagrant ssh node2
sudo ansible-playbook -i /vagrant/ansible/hosts.ini /vagrant/ansible/site.yml

# 특정 태그만 실행
sudo ansible-playbook -i /vagrant/ansible/hosts.ini /vagrant/ansible/site.yml --tags "ssh"
sudo ansible-playbook -i /vagrant/ansible/hosts.ini /vagrant/ansible/site.yml --tags "storage,systemd"
```

### 로그 확인

```bash
# Vagrant 로그
vagrant up --debug > vagrant.log 2>&1

# Ansible 로그 (VM 내부)
vagrant ssh node2
sudo cat /var/log/ansible.log

# Systemd 로그
vagrant ssh node1
sudo journalctl -xe
```

## 성능 최적화

### VirtualBox 설정

```bash
# VM 리소스 증가 (Vagrantfile 수정 후)
# vb.memory = "12288"  # 12GB
# vb.cpus = 4          # 4 CPU

vagrant reload
```

### 디스크 I/O 최적화

```bash
# SSD 사용 권장
# VirtualBox 설정에서 디스크 캐시 활성화
VBoxManage storageattach rac-node1 --storagectl "SATA Controller" --port 0 --device 0 --nonrotational on --discard on
```

### 네트워크 최적화

```bash
# VirtualBox 네트워크 어댑터 타입 변경
# Vagrantfile에서:
# node1.vm.network "private_network", ip: "192.168.1.101", nic_type: "virtio"
```

## 백업 및 복구

### VM 스냅샷

```bash
# 스냅샷 생성
VBoxManage snapshot rac-node1 take "before_grid_install" --description "Before Grid Infrastructure installation"
VBoxManage snapshot rac-node2 take "before_grid_install" --description "Before Grid Infrastructure installation"

# 스냅샷 목록 확인
VBoxManage snapshot rac-node1 list

# 스냅샷 복원
VBoxManage snapshot rac-node1 restore "before_grid_install"
VBoxManage snapshot rac-node2 restore "before_grid_install"

# 스냅샷 삭제
VBoxManage snapshot rac-node1 delete "before_grid_install"
```

### 구성 백업

```bash
# Vagrantfile 및 Ansible 구성 백업
tar -czf oracle-rac-config-$(date +%Y%m%d).tar.gz Vagrantfile ansible/ tests/

# 백업 복원
tar -xzf oracle-rac-config-20240308.tar.gz
```

## 다음 단계

구성이 완료되면 다음 단계로 진행하세요:

1. [Oracle 19.19 RU 적용](ORACLE_RU.md)
2. [Oracle Grid Infrastructure 설치](ORACLE_RU.md#grid-infrastructure-설치)
3. [Oracle Database 설치](ORACLE_RU.md#database-설치)

## 문제 해결

문제가 발생한 경우 [트러블슈팅 가이드](TROUBLESHOOTING.md)를 참조하세요.

