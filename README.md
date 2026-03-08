# Oracle RAC Vagrant Setup

로컬 개발 환경에서 Oracle 19c RAC(Real Application Clusters) 2노드 클러스터를 자동으로 배포하는 Infrastructure as Code 프로젝트입니다.

## 프로젝트 개요

본 프로젝트는 Vagrant와 Ansible을 사용하여 Rocky Linux 9 기반의 Oracle 19c RAC 2노드 클러스터를 완전 자동화된 방식으로 구성합니다.

### 주요 특징

- **완전 자동화**: 수동 개입 없이 RAC 클러스터 환경 구성
- **멱등성 보장**: 반복 실행 시 동일한 결과 생성
- **Infrastructure as Code**: 버전 관리 가능한 선언적 구성
- **Rocky Linux 9 호환**: Oracle 19.19+ RU 사용

### 시스템 구성

- **VM 프로비저닝**: Vagrant + VirtualBox
- **OS 구성 자동화**: Ansible (node2를 control node로 사용)
- **베이스 OS**: Rocky Linux 9
- **Oracle 버전**: 19c (19.19+ RU 필요)
- **클러스터 구성**: 2노드 RAC

## 시스템 요구사항

### 호스트 시스템

- **OS**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+, CentOS 8+)
- **CPU**: 4코어 이상 권장 (Intel VT-x 또는 AMD-V 가상화 지원 필수)
- **메모리**: 최소 20GB RAM
  - VM 2개 × 8GB = 16GB
  - 호스트 OS = 4GB
  - 권장: 24GB 이상
- **디스크 공간**: 최소 100GB 여유 공간
  - VM 디스크: 약 40GB
  - ASM 공유 디스크: 50GB
  - Oracle 소프트웨어: 10GB

### 필수 소프트웨어

#### 1. VirtualBox 설치
- **버전**: 6.1 이상 (7.0 권장)
- **다운로드**: https://www.virtualbox.org/wiki/Downloads
- **설치 확인**:
  ```bash
  VBoxManage --version
  ```

#### 2. Vagrant 설치
- **버전**: 2.2 이상 (2.3+ 권장)
- **다운로드**: https://www.vagrantup.com/downloads
- **설치 확인**:
  ```bash
  vagrant --version
  ```

#### 3. Oracle 소프트웨어 (별도 다운로드 필요)
- Oracle 19c Grid Infrastructure (19.19+ RU)
- Oracle 19c Database (19.19+ RU)
- **다운로드**: https://www.oracle.com/database/technologies/oracle19c-linux-downloads.html
- **중요**: Rocky Linux 9 호환성을 위해 19.19 이상 RU 필수

### 실행 전 체크리스트

#### ✅ 하드웨어 요구사항
- [ ] CPU 가상화 지원 활성화 (BIOS에서 Intel VT-x 또는 AMD-V 활성화)
- [ ] 최소 20GB RAM 사용 가능
- [ ] 최소 100GB 디스크 여유 공간

#### ✅ 소프트웨어 설치
- [ ] VirtualBox 6.1+ 설치 완료
- [ ] Vagrant 2.2+ 설치 완료
- [ ] Git 설치 완료 (프로젝트 클론용)

#### ✅ 네트워크 설정
- [ ] 192.168.1.0/24 대역이 호스트 네트워크와 충돌하지 않음
- [ ] VirtualBox Host-Only 네트워크 어댑터 사용 가능

#### ✅ 권한 확인
- [ ] VirtualBox 실행 권한 (관리자 권한 필요할 수 있음)
- [ ] Vagrant 실행 권한

### 예상 소요 시간

- **VM 프로비저닝**: 5-10분
- **Ansible 구성**: 10-15분
- **전체 프로세스**: 15-25분 (네트워크 속도에 따라 다름)

## 네트워크 구성

### Public Network (192.168.1.0/24)
- node1: 192.168.1.101
- node2: 192.168.1.102
- node1-vip: 192.168.1.111
- node2-vip: 192.168.1.112
- rac-scan: 192.168.1.121-123

### Private Network (10.0.0.0/24)
- node1-priv: 10.0.0.101
- node2-priv: 10.0.0.102

## 빠른 시작 가이드

### 1단계: 프로젝트 클론

```bash
git clone https://github.com/zapan1015/oracle19c_rocky9.git
cd oracle19c_rocky9
```

### 2단계: 실행 전 확인

```bash
# VirtualBox 버전 확인
VBoxManage --version

# Vagrant 버전 확인
vagrant --version

# 디스크 공간 확인 (Windows)
wmic logicaldisk get size,freespace,caption

# 디스크 공간 확인 (Linux/Mac)
df -h .
```

### 3단계: VM 프로비저닝 및 자동 구성

```bash
# 전체 프로세스 시작 (15-25분 소요)
vagrant up

# 진행 상황 모니터링
# - VM 생성 및 부팅
# - 네트워크 구성
# - DNS 설정
# - Ansible 환경 준비
# - OS 레벨 구성 (사용자, 패키지, 보안, SSH, 스토리지, systemd)
```

**실행 중 출력 예시**:
```
Bringing machine 'node1' up with 'virtualbox' provider...
Bringing machine 'node2' up with 'virtualbox' provider...
==> node1: Importing base box 'rockylinux/9'...
==> node1: Configuring network adapters...
==> node2: Running provisioner: shell (setup_hosts.sh)...
==> node2: Running provisioner: shell (setup_dnsmasq.sh)...
==> node2: Running provisioner: ansible_local (site.yml)...
```

### 4단계: 구성 검증

#### Python 기반 Property 테스트 (Host에서 실행)

```bash
# Python 및 pytest 설치 (처음 한 번만)
pip install -r tests/requirements.txt

# 모든 Property 테스트 실행 (100회 반복)
pytest tests/ -v

# 특정 테스트만 실행
pytest tests/test_vagrantfile_properties.py -v
pytest tests/test_dns_properties.py -v
pytest tests/test_oracle_users_groups_properties.py -v
```

#### Bash 검증 스크립트 (VM 내부에서 실행)

```bash
# node2에서 모든 검증 스크립트 실행
vagrant ssh node2 -c "bash /vagrant/tests/verify_all.sh"

# 개별 검증
vagrant ssh node2 -c "bash /vagrant/tests/verify_network.sh"
vagrant ssh node2 -c "bash /vagrant/tests/verify_dns.sh"
vagrant ssh node2 -c "bash /vagrant/tests/verify_ssh.sh"
vagrant ssh node2 -c "bash /vagrant/tests/verify_storage.sh"
vagrant ssh node2 -c "bash /vagrant/tests/verify_system.sh"
```

### 5단계: VM 접속

```bash
# node1 접속
vagrant ssh node1

# node2 접속
vagrant ssh node2

# root 사용자로 전환
sudo su -

# grid 사용자로 전환
sudo su - grid

# oracle 사용자로 전환
sudo su - oracle
```

### 6단계: Oracle Grid Infrastructure 설치

VM 구성이 완료되면 Oracle Grid Infrastructure를 설치할 수 있습니다.

```bash
# 1. Oracle 소프트웨어를 VM에 복사
# Host에서 실행 (예시)
scp LINUX.X64_193000_grid_home.zip vagrant@192.168.1.101:/tmp/

# 2. node1에서 grid 사용자로 실행
vagrant ssh node1
sudo su - grid
cd /u01/app/19.3.0/grid

# 3. Grid Infrastructure 압축 해제
unzip -q /tmp/LINUX.X64_193000_grid_home.zip

# 4. RU 패치 적용 (19.19+ 필수)
./gridSetup.sh -applyRU /path/to/ru_patch

# 5. Silent 모드로 설치
./gridSetup.sh -silent -responseFile /vagrant/response/grid_install.rsp
```

자세한 내용은 [Oracle RU 적용 가이드](docs/ORACLE_RU.md)를 참조하세요.

## 프로젝트 구조

```
oracle-rac-vagrant-setup/
├── Vagrantfile              # VM 프로비저닝 정의
├── ansible/                 # Ansible 구성 파일
│   ├── hosts.ini           # 인벤토리 파일
│   ├── site.yml            # 메인 플레이북
│   ├── group_vars/         # 그룹 변수
│   └── roles/              # Ansible 역할
├── tests/                   # 검증 스크립트
│   ├── verify_all.sh       # 통합 검증
│   ├── verify_network.sh   # 네트워크 검증
│   ├── verify_dns.sh       # DNS 검증
│   ├── verify_ssh.sh       # SSH 검증
│   ├── verify_storage.sh   # 스토리지 검증
│   └── verify_system.sh    # 시스템 검증
├── docs/                    # 문서
│   ├── USAGE.md            # 사용 가이드
│   ├── ORACLE_RU.md        # Oracle RU 적용 가이드
│   ├── TROUBLESHOOTING.md  # 트러블슈팅
│   └── ARCHITECTURE.md     # 아키텍처 문서
└── README.md               # 본 파일
```

## 배포 프로세스

### Phase 1: Vagrant 프로비저닝
1. VirtualBox를 통한 VM 생성 (node1, node2)
2. 네트워크 인터페이스 구성 (Public + Private)
3. 공유 스토리지 연결 (ASM 디스크)
4. DNS 서버 설정 (dnsmasq on node2)

### Phase 2: Ansible 구성
1. Oracle 사용자 및 그룹 생성
2. Oracle Preinstall 패키지 설치
3. 보안 구성 (방화벽, SELinux, SSH)
4. SSH User Equivalence 설정
5. 시간 동기화 (chrony)
6. 공유 스토리지 구성 (udev rules)
7. 커널 매개변수 및 리소스 제한 설정
8. Systemd 및 Cgroup v2 구성

## 주요 명령어

### VM 관리

```bash
# VM 시작 (처음 실행 시 자동 프로비저닝)
vagrant up

# VM 중지 (데이터 유지)
vagrant halt

# VM 재시작
vagrant reload

# VM 재프로비저닝 (구성 재적용)
vagrant provision

# VM 삭제 (완전 초기화, 데이터 삭제)
vagrant destroy

# VM 상태 확인
vagrant status

# 모든 VM 상태 확인
vagrant global-status
```

### 문제 해결

```bash
# VM 완전 재시작
vagrant destroy -f && vagrant up

# 특정 VM만 재시작
vagrant destroy node1 -f && vagrant up node1

# Ansible 플레이북만 재실행 (node2에서)
vagrant ssh node2
sudo ansible-playbook -i /vagrant/ansible/hosts.ini /vagrant/ansible/site.yml

# 특정 태그만 실행
sudo ansible-playbook -i /vagrant/ansible/hosts.ini /vagrant/ansible/site.yml --tags "ssh,storage"

# 로그 확인
vagrant up --debug > vagrant.log 2>&1
```

### 테스트 실행

```bash
# Host에서 Python 테스트 실행
pytest tests/ -v --tb=short

# VM 내부에서 검증 스크립트 실행
vagrant ssh node2 -c "bash /vagrant/tests/verify_all.sh"

# 특정 Property 테스트
pytest tests/test_vagrantfile_properties.py::test_property_1_vm_configuration_consistency -v
```

### 유용한 명령어

```bash
# VM 스냅샷 생성 (VirtualBox 직접 사용)
VBoxManage snapshot rac-node1 take "before_grid_install"
VBoxManage snapshot rac-node2 take "before_grid_install"

# 스냅샷 복원
VBoxManage snapshot rac-node1 restore "before_grid_install"
VBoxManage snapshot rac-node2 restore "before_grid_install"

# VM 리소스 확인
vagrant ssh node1 -c "free -h && df -h && lscpu"

# 네트워크 연결 테스트
vagrant ssh node1 -c "ping -c 3 192.168.1.102"
vagrant ssh node1 -c "ping -c 3 10.0.0.102"
```

## 트러블슈팅

문제가 발생한 경우 [트러블슈팅 가이드](docs/TROUBLESHOOTING.md)를 참조하세요.

### 일반적인 문제

1. **VM 생성 실패**: VirtualBox 버전 확인 및 가상화 지원 확인
2. **네트워크 연결 실패**: 호스트 네트워크 어댑터 설정 확인
3. **공유 스토리지 접근 불가**: udev rules 재적용 필요
4. **Ansible 실행 실패**: SSH 연결 및 권한 확인

## 라이선스

본 프로젝트는 교육 및 개발 목적으로 제공됩니다. Oracle 소프트웨어는 별도의 라이선스가 필요합니다.

## 참고 자료

- [Oracle Database 19c Documentation](https://docs.oracle.com/en/database/oracle/oracle-database/19/)
- [Oracle RAC Installation Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/rilin/)
- [Rocky Linux Documentation](https://docs.rockylinux.org/)
- [Vagrant Documentation](https://www.vagrantup.com/docs)
- [Ansible Documentation](https://docs.ansible.com/)

## 기여

이슈 및 풀 리퀘스트를 환영합니다.

## 지원

문제가 발생하거나 질문이 있는 경우 이슈를 생성해 주세요.
