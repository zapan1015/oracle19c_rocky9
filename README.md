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

- **OS**: Windows, macOS, Linux
- **CPU**: 4코어 이상 권장
- **메모리**: 최소 20GB (VM 2개 × 8GB + 호스트 4GB)
- **디스크 공간**: 최소 100GB 여유 공간

### 필수 소프트웨어

- [VirtualBox](https://www.virtualbox.org/) 6.1 이상
- [Vagrant](https://www.vagrantup.com/) 2.2 이상
- Oracle 19c Grid Infrastructure 및 Database 소프트웨어 (19.19+ RU)

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

## 사용 방법

### 1. 프로젝트 클론

```bash
git clone <repository-url>
cd oracle-rac-vagrant-setup
```

### 2. VM 프로비저닝 및 구성

```bash
# VM 생성 및 자동 구성 시작
vagrant up

# 프로비저닝 완료까지 약 15-20분 소요
```

### 3. 구성 검증

```bash
# 모든 검증 스크립트 실행
./tests/verify_all.sh

# 개별 검증
./tests/verify_network.sh   # 네트워크 연결성
./tests/verify_dns.sh        # DNS 해석
./tests/verify_ssh.sh        # SSH User Equivalence
./tests/verify_storage.sh    # 공유 스토리지
./tests/verify_system.sh     # 시스템 구성
```

### 4. VM 접속

```bash
# node1 접속
vagrant ssh node1

# node2 접속
vagrant ssh node2
```

### 5. Oracle Grid Infrastructure 설치

VM 구성이 완료되면 Oracle Grid Infrastructure를 설치할 수 있습니다.

```bash
# node1에서 grid 사용자로 실행
vagrant ssh node1
sudo su - grid
cd /u01/app/19.3.0/grid

# Silent 모드로 Grid Infrastructure 설치
./gridSetup.sh -silent -responseFile /path/to/grid_install.rsp
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

```bash
# VM 시작
vagrant up

# VM 중지
vagrant halt

# VM 재시작
vagrant reload

# VM 삭제 (완전 초기화)
vagrant destroy

# VM 상태 확인
vagrant status

# Ansible 플레이북 재실행 (node2에서)
vagrant ssh node2
ansible-playbook -i /vagrant/ansible/hosts.ini /vagrant/ansible/site.yml
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
