# 요구사항 문서

## 소개

본 문서는 로컬 개발 환경에서 Oracle 19c RAC(Real Application Clusters) 2노드 클러스터를 자동으로 배포하는 시스템의 요구사항을 명세합니다. 이 시스템은 Rocky Linux 9 기반 VM 프로비저닝을 위해 Vagrant를 사용하며, RAC 2번 노드(node2)에서 실행되는 Ansible을 통해 자동화된 구성 관리를 수행합니다.

배포 프로세스는 두 단계로 구성됩니다:
1. Vagrant 단계: VM 프로비저닝, 네트워크 인터페이스 구성, DNS 설정 (요구사항 1-3)
2. Ansible 단계: node2를 Ansible control node로 사용하여 node1과 node2를 모두 구성 (요구사항 4-11)

node2에서 실행되는 Ansible은 단일 제어 지점에서 두 노드에 대한 사용자/그룹 구성, 패키지 설치, 보안 설정, SSH 구성, 스토리지 설정 등 모든 OS 레벨 구성을 동시에 적용합니다. 이를 통해 휴먼 에러를 원천 차단하고 재현 가능한 환경 구성을 보장합니다.

본 시스템은 Infrastructure as Code(IaC) 원칙을 따르며, 멱등성(Idempotency) 보장을 목표로 합니다. Oracle 19.19 이상 Release Update를 사용하여 Rocky Linux 9와의 호환성을 보장합니다.

## 용어 정의

- **RAC_System**: VM, 네트워킹, 자동화를 포함한 전체 Oracle 19c Real Application Clusters 배포 시스템
- **Vagrant_Provisioner**: VirtualBox VM을 생성하고 구성하는 Vagrant 컴포넌트
- **Ansible_Configurator**: node2에서 RAC 노드를 구성하는 Ansible 자동화 컴포넌트
- **Network_Manager**: 네트워크 인터페이스, DNS, IP 구성을 관리하는 컴포넌트
- **Storage_Manager**: ASM(Automatic Storage Management)용 공유 스토리지를 관리하는 컴포넌트
- **Security_Configurator**: 방화벽, SELinux, SSH 구성을 관리하는 컴포넌트
- **Systemd_Configurator**: Rocky Linux 9의 systemd 및 cgroup v2 리소스 제어를 관리하는 컴포넌트
- **DNS_Server**: SCAN 이름 해석을 제공하는 dnsmasq 기반 DNS 서버
- **Grid_Infrastructure**: RAC 클러스터링을 위한 Oracle Grid Infrastructure 소프트웨어
- **Public_Network**: 클라이언트 연결을 위한 외부 네트워크 (private_network 타입, 192.168.1.x 대역)
- **Private_Network**: 노드 인터커넥트를 위한 내부 네트워크 (virtualbox__intnet 옵션 사용)
- **SCAN**: Single Client Access Name - RAC를 위한 DNS 기반 로드 밸런싱 메커니즘
- **VIP**: 노드 장애조치 기능을 위한 가상 IP 주소
- **ASM**: Oracle 데이터베이스 스토리지를 위한 Automatic Storage Management
- **ASM_Disk**: ASM에서 사용하는 공유 디스크 (udev rules로 관리, ASMLib 미사용)
- **User_Equivalence**: RAC 노드 간 SSH 비밀번호 없는 인증 (2048 bits 키 사용)

## 요구사항

### 요구사항 1: Vagrant를 통한 VM 프로비저닝

**사용자 스토리:** 개발자로서, Vagrant를 사용하여 두 개의 Rocky Linux 9 VM을 프로비저닝하여, 로컬에서 일관된 RAC 클러스터 환경을 생성하고 싶습니다.

#### 인수 기준

1. THE Vagrant_Provisioner SHALL rockylinux/9 베이스 이미지를 사용하여 두 개의 VM을 생성한다
2. WHEN 프로비저닝이 시작되면, THE Vagrant_Provisioner SHALL 각 VM을 8GB RAM으로 구성한다
3. WHEN 프로비저닝이 시작되면, THE Vagrant_Provisioner SHALL 각 VM을 최소 2 CPU 코어로 구성한다
4. THE Vagrant_Provisioner SHALL 각 VM에 두 개의 네트워크 어댑터를 연결한다
5. THE Vagrant_Provisioner SHALL 두 VM이 모두 접근 가능한 공유 스토리지 장치를 구성한다
6. WHEN 프로비저닝이 완료되면, THE Vagrant_Provisioner SHALL 두 VM이 모두 실행 상태임을 보장한다
7. THE Vagrant_Provisioner SHALL 멱등성을 보장하여 반복 실행 시 동일한 결과를 생성한다

### 요구사항 2: 네트워크 인터페이스 구성

**사용자 스토리:** 시스템 관리자로서, 각 노드에 적절하게 구성된 네트워크 인터페이스를 원하여, RAC가 클라이언트 접근과 클러스터 인터커넥트 모두에 대해 올바르게 통신할 수 있도록 하고 싶습니다.

#### 인수 기준

1. THE Network_Manager SHALL Adapter 1을 private_network 타입의 Public_Network로 구성한다
2. THE Network_Manager SHALL Adapter 2를 virtualbox__intnet 옵션을 사용하는 Private_Network로 구성한다
3. THE Network_Manager SHALL node1 Public_Network에 고정 IP 192.168.1.101을 할당한다
4. THE Network_Manager SHALL node2 Public_Network에 고정 IP 192.168.1.102를 할당한다
5. THE Network_Manager SHALL node1 Private_Network에 고정 IP 10.0.0.101을 할당한다
6. THE Network_Manager SHALL node2 Private_Network에 고정 IP 10.0.0.102를 할당한다
7. THE Network_Manager SHALL Private_Network를 내부 네트워크로 명시적으로 구성한다
8. WHEN 네트워크 구성이 완료되면, THE Network_Manager SHALL 두 네트워크 모두에서 노드 간 연결성을 검증한다

### 요구사항 3: DNS 및 SCAN 구성

**사용자 스토리:** 데이터베이스 관리자로서, SCAN DNS 해석이 구성되어, 클라이언트가 로드 밸런싱과 함께 단일 이름을 사용하여 RAC 클러스터에 연결할 수 있도록 하고 싶습니다.

#### 인수 기준

1. THE DNS_Server SHALL 최소 한 노드에 dnsmasq를 설치하고 구성한다
2. THE DNS_Server SHALL rac-scan.localdomain을 세 개의 IP 주소로 해석한다: 192.168.1.121, 192.168.1.122, 192.168.1.123
3. THE DNS_Server SHALL SCAN 이름 해석을 위해 라운드 로빈 DNS를 구현한다
4. THE DNS_Server SHALL node1-vip.localdomain을 192.168.1.111로 해석한다
5. THE DNS_Server SHALL node2-vip.localdomain을 192.168.1.112로 해석한다
6. THE DNS_Server SHALL node1.localdomain을 192.168.1.101로 해석한다
7. THE DNS_Server SHALL node2.localdomain을 192.168.1.102로 해석한다
8. THE DNS_Server SHALL node1-priv.localdomain을 10.0.0.101로 해석한다
9. THE DNS_Server SHALL node2-priv.localdomain을 10.0.0.102로 해석한다
10. WHEN DNS 구성이 완료되면, THE DNS_Server SHALL 모든 이름 해석이 올바른 IP 주소를 반환하는지 검증한다

### 요구사항 4: Oracle 사용자 및 그룹 구성

**사용자 스토리:** 시스템 관리자로서, 역할 분리를 통해 Oracle 사용자와 그룹이 구성되어, Grid Infrastructure와 Database 소프트웨어가 적절한 소유권과 권한을 갖도록 하고 싶습니다.

#### 인수 기준

1. THE Ansible_Configurator SHALL node2에서 실행되어 node1과 node2 두 노드에 GID 54321로 oinstall 그룹을 생성한다
2. THE Ansible_Configurator SHALL 두 노드에 GID 54322로 dba 그룹을 생성한다
3. THE Ansible_Configurator SHALL 두 노드에 GID 54327로 asmdba 그룹을 생성한다
4. THE Ansible_Configurator SHALL 두 노드에 GID 54328로 asmoper 그룹을 생성한다
5. THE Ansible_Configurator SHALL 두 노드에 GID 54329로 asmadmin 그룹을 생성한다
6. THE Ansible_Configurator SHALL 두 노드에 UID 54331과 기본 그룹 oinstall로 grid 사용자를 생성한다
7. THE Ansible_Configurator SHALL 두 노드에 UID 54321과 기본 그룹 oinstall로 oracle 사용자를 생성한다
8. THE Ansible_Configurator SHALL 두 노드에서 grid 사용자를 asmadmin, asmdba, asmoper 그룹에 추가한다
9. THE Ansible_Configurator SHALL 두 노드에서 oracle 사용자를 dba, asmdba, asmadmin 그룹에 추가한다
10. THE Ansible_Configurator SHALL 두 노드에 소유자 grid와 그룹 oinstall로 디렉토리 /u01/app/grid를 생성한다
11. THE Ansible_Configurator SHALL 두 노드에 소유자 grid와 그룹 oinstall로 디렉토리 /u01/app/19.3.0/grid를 생성한다
12. THE Ansible_Configurator SHALL 두 노드에 소유자 oracle과 그룹 oinstall로 디렉토리 /u01/app/oracle을 생성한다
13. THE Ansible_Configurator SHALL 두 노드에 소유자 oracle과 그룹 oinstall로 디렉토리 /u01/app/oracle/product/19.3.0/dbhome_1을 생성한다

### 요구사항 5: Oracle Preinstall 패키지 설치

**사용자 스토리:** 시스템 관리자로서, Oracle preinstall 패키지가 설치되어, Rocky Linux 9에서 Oracle 19c를 위한 모든 OS 전제 조건이 충족되도록 하고 싶습니다.

#### 인수 기준

1. THE Ansible_Configurator SHALL 두 노드에 oracle-database-preinstall-19c 패키지를 설치한다
2. WHEN oracle-database-preinstall-19c 설치가 완료되면, THE Ansible_Configurator SHALL 커널 매개변수가 올바르게 구성되었는지 검증한다
3. WHEN oracle-database-preinstall-19c 설치가 완료되면, THE Ansible_Configurator SHALL 리소스 제한이 올바르게 구성되었는지 검증한다
4. THE Ansible_Configurator SHALL Oracle 19c RAC에 필요한 모든 RPM 패키지를 설치한다
5. THE Ansible_Configurator SHALL Rocky Linux 9 호환성을 위해 Oracle 19.19 이상 RU 요구사항을 문서화한다

### 요구사항 6: 보안 구성

**사용자 스토리:** 시스템 관리자로서, RAC에 적합하게 보안 설정이 구성되어, 클러스터가 합리적인 보호를 유지하면서 보안 간섭 없이 작동할 수 있도록 하고 싶습니다.

#### 인수 기준

1. THE Security_Configurator SHALL node2에서 실행되어 두 노드에서 firewalld 서비스를 비활성화한다
2. THE Security_Configurator SHALL 두 노드에서 SELinux를 permissive 모드로 설정한다
3. WHEN SELinux 모드가 변경되면, THE Security_Configurator SHALL 두 노드에서 재부팅 후에도 구성이 유지되도록 한다
4. THE Security_Configurator SHALL 두 노드에서 초기 설정을 위해 root 로그인을 허용하도록 SSH를 구성한다

### 요구사항 7: SSH User Equivalence

**사용자 스토리:** 데이터베이스 관리자로서, grid 및 oracle 사용자를 위해 노드 간 비밀번호 없는 SSH가 구성되어, RAC 설치 및 운영이 수동 인증 없이 진행될 수 있도록 하고 싶습니다.

#### 인수 기준

1. THE Security_Configurator SHALL node2에서 실행되어 두 노드에서 grid 사용자를 위한 2048 bits SSH 키 쌍을 생성한다
2. THE Security_Configurator SHALL 두 노드에서 oracle 사용자를 위한 2048 bits SSH 키 쌍을 생성한다
3. THE Security_Configurator SHALL authorized_keys 모듈을 사용하여 두 노드에 grid 사용자 공개 키를 자동 배포한다
4. THE Security_Configurator SHALL authorized_keys 모듈을 사용하여 두 노드에 oracle 사용자 공개 키를 자동 배포한다
5. THE Security_Configurator SHALL SSH User_Equivalence 구성의 멱등성을 보장한다
6. WHEN SSH 구성이 완료되면, THE Security_Configurator SHALL grid 사용자가 node1에서 node2로 비밀번호 없이 SSH 접속할 수 있는지 검증한다
7. WHEN SSH 구성이 완료되면, THE Security_Configurator SHALL grid 사용자가 node2에서 node1로 비밀번호 없이 SSH 접속할 수 있는지 검증한다
8. WHEN SSH 구성이 완료되면, THE Security_Configurator SHALL oracle 사용자가 node1에서 node2로 비밀번호 없이 SSH 접속할 수 있는지 검증한다
9. WHEN SSH 구성이 완료되면, THE Security_Configurator SHALL oracle 사용자가 node2에서 node1로 비밀번호 없이 SSH 접속할 수 있는지 검증한다

### 요구사항 8: 시간 동기화

**사용자 스토리:** 시스템 관리자로서, RAC 노드 간 시간이 동기화되어, 클러스터 작업과 로그 타임스탬프가 일관되도록 하고 싶습니다.

#### 인수 기준

1. THE Ansible_Configurator SHALL node2에서 실행되어 두 노드에 chrony를 설치하고 구성한다
2. THE Ansible_Configurator SHALL 두 노드에서 동일한 NTP 서버를 사용하도록 chrony를 구성한다
3. WHEN chrony 구성이 완료되면, THE Ansible_Configurator SHALL 노드 간 시간 차이가 1초 미만인지 검증한다
4. THE Ansible_Configurator SHALL 두 노드에서 부팅 시 chrony 서비스가 시작되도록 활성화한다

### 요구사항 9: 공유 스토리지 구성

**사용자 스토리:** 데이터베이스 관리자로서, ASM을 위한 공유 스토리지가 구성되어, Grid Infrastructure가 클러스터 전체에서 데이터베이스 파일을 관리할 수 있도록 하고 싶습니다.

#### 인수 기준

1. THE Storage_Manager SHALL VirtualBox SATA Controller를 사용하여 공유 디스크를 연결한다
2. THE Storage_Manager SHALL 20GB 크기의 asm_disk1을 DATA 디스크 그룹용으로 생성한다
3. THE Storage_Manager SHALL 20GB 크기의 asm_disk2를 DATA 디스크 그룹용으로 생성한다
4. THE Storage_Manager SHALL 10GB 크기의 asm_disk3을 FRA(Fast Recovery Area) 디스크 그룹용으로 생성한다
5. THE Storage_Manager SHALL 모든 ASM_Disk를 Fixed variant로 생성하여 성능과 안정성을 보장한다
6. THE Storage_Manager SHALL 모든 ASM_Disk를 Shareable type으로 구성하여 PRVF-5150 에러를 방지한다
7. THE Ansible_Configurator SHALL node2에서 실행되어 ASMLib 대신 네이티브 udev rules를 사용하여 두 노드의 ASM_Disk를 관리한다
8. THE Ansible_Configurator SHALL 두 노드에서 /dev/sdb에 대한 udev rule을 생성하여 소유자 grid, 그룹 asmadmin, 권한 0660으로 설정한다
9. THE Ansible_Configurator SHALL 두 노드에서 /dev/sdc에 대한 udev rule을 생성하여 소유자 grid, 그룹 asmadmin, 권한 0660으로 설정한다
10. THE Ansible_Configurator SHALL 두 노드에서 /dev/sdd에 대한 udev rule을 생성하여 소유자 grid, 그룹 asmadmin, 권한 0660으로 설정한다
11. THE Ansible_Configurator SHALL 두 노드에서 재부팅 후에도 일관된 디스크 장치 이름을 유지하도록 udev 규칙을 구성한다
12. WHEN 스토리지 구성이 완료되면, THE Storage_Manager SHALL 두 노드가 모든 공유 디스크에 접근할 수 있는지 검증한다

### 요구사항 10: 커널 매개변수 및 리소스 제한

**사용자 스토리:** 시스템 관리자로서, Oracle 19c를 위한 커널 매개변수와 리소스 제한이 구성되어, 데이터베이스가 최적의 성능과 안정성으로 작동할 수 있도록 하고 싶습니다.

#### 인수 기준

1. THE Ansible_Configurator SHALL node2에서 실행되어 두 노드에서 kernel.shmmax를 최소 4398046511104로 구성한다
2. THE Ansible_Configurator SHALL 두 노드에서 kernel.shmall을 최소 1073741824로 구성한다
3. THE Ansible_Configurator SHALL 두 노드에서 kernel.shmmni를 최소 4096으로 구성한다
4. THE Ansible_Configurator SHALL 두 노드에서 fs.file-max를 최소 6815744로 구성한다
5. THE Ansible_Configurator SHALL 두 노드에서 net.ipv4.ip_local_port_range를 9000 65500으로 구성한다
6. THE Ansible_Configurator SHALL 두 노드에서 grid 및 oracle 사용자를 위해 soft nofile 제한을 1024로 구성한다
7. THE Ansible_Configurator SHALL 두 노드에서 grid 및 oracle 사용자를 위해 hard nofile 제한을 65536으로 구성한다
8. THE Ansible_Configurator SHALL 두 노드에서 grid 및 oracle 사용자를 위해 soft nproc 제한을 16384로 구성한다
9. THE Ansible_Configurator SHALL 두 노드에서 grid 및 oracle 사용자를 위해 hard nproc 제한을 16384로 구성한다
10. WHEN 구성이 완료되면, THE Ansible_Configurator SHALL 두 노드에서 모든 매개변수가 재부팅 후에도 유지되는지 검증한다

### 요구사항 11: Systemd 및 Cgroup 구성

**사용자 스토리:** 시스템 관리자로서, Oracle 19c 호환성을 위해 systemd와 cgroup v2가 구성되어, Rocky Linux 9에서 리소스 관리가 올바르게 작동하도록 하고 싶습니다.

#### 인수 기준

1. WHERE Rocky Linux 9가 cgroup v2를 사용하는 경우, THE Systemd_Configurator SHALL node2에서 실행되어 두 노드에 systemd 리소스 제어 설정을 구성한다
2. THE Systemd_Configurator SHALL 두 노드에서 /etc/systemd/system.conf에 DefaultTasksMax=infinity를 구성한다
3. THE Systemd_Configurator SHALL 두 노드에서 /etc/systemd/system.conf에 DefaultMemoryAccounting=yes를 구성한다
4. THE Systemd_Configurator SHALL 두 노드에서 /etc/systemd/logind.conf에 RemoveIPC=no를 구성한다
5. THE Systemd_Configurator SHALL 두 노드에서 OOM Killer 및 Node Eviction을 방지하기 위한 설정을 구성한다
6. WHEN systemd 구성이 변경되면, THE Systemd_Configurator SHALL 두 노드에서 systemd 구성을 다시 로드한다
7. THE Systemd_Configurator SHALL 두 노드에서 cgroup 설정이 Oracle 19c 요구사항과 호환되는지 검증한다

### 요구사항 12: Node2에서 Ansible 실행 환경 구성

**사용자 스토리:** 개발자로서, node2에 Ansible 실행 환경이 구성되어, 단일 제어 지점에서 전체 RAC 클러스터를 자동으로 구성할 수 있도록 하고 싶습니다.

#### 인수 기준

1. THE Ansible_Configurator SHALL node2에 Ansible을 설치한다
2. THE Ansible_Configurator SHALL node1과 node2를 포함하는 Ansible 인벤토리를 구성한다
3. THE Ansible_Configurator SHALL node2를 Ansible control node로 구성한다
4. THE Ansible_Configurator SHALL node1과 node2를 Ansible managed nodes로 구성한다
5. THE Ansible_Configurator SHALL node2에서 node1로 연결하기 위해 SSH를 사용한다
6. WHEN Ansible 플레이북이 실행되면, THE Ansible_Configurator SHALL 두 노드에 구성을 동시에 적용한다
7. WHEN Ansible 실행이 완료되면, THE Ansible_Configurator SHALL 각 구성 작업의 성공 또는 실패를 보고한다
8. THE Ansible_Configurator SHALL 요구사항 4-11의 모든 구성 작업을 node2에서 실행하여 두 노드에 적용한다

### 요구사항 13: Oracle 19.19 RU 호환성 검증

**사용자 스토리:** 데이터베이스 관리자로서, Oracle 19.19 이상 RU가 필요함을 검증하여, 설치가 Rocky Linux 9와 호환되도록 하고 싶습니다.

#### 인수 기준

1. THE RAC_System SHALL Oracle 19.19 이상 Release Update 요구사항을 문서화한다
2. THE RAC_System SHALL gridSetup.sh -applyRU 옵션을 사용한 RU 적용 방법을 문서화한다
3. WHEN Oracle 소프트웨어가 준비되면, THE RAC_System SHALL 버전이 19.19 이상인지 검증한다
4. IF Oracle 소프트웨어 버전이 19.19 미만이면, THEN THE RAC_System SHALL Rocky Linux 9 호환성을 위해 19.19 이상이 필요함을 나타내는 오류 메시지를 표시한다

### 요구사항 14: Infrastructure as Code 원칙 준수

**사용자 스토리:** 개발자로서, IaC 원칙을 따르는 자동화 시스템을 원하여, 휴먼 에러를 원천 차단하고 재현 가능한 환경을 구성하고 싶습니다.

#### 인수 기준

1. THE RAC_System SHALL 모든 구성 작업에 대해 멱등성을 보장한다
2. THE RAC_System SHALL 수동 개입 없이 완전 자동화된 배포를 수행한다
3. THE RAC_System SHALL Silent 모드를 사용하여 Oracle Grid Infrastructure 설치를 자동화한다
4. THE RAC_System SHALL 모든 구성을 코드로 관리하여 버전 관리가 가능하도록 한다
5. WHEN 동일한 구성으로 재실행되면, THE RAC_System SHALL 동일한 결과를 생성한다
6. THE RAC_System SHALL 휴먼 에러 가능성을 최소화하기 위해 수동 단계를 제거한다

### 요구사항 15: 설치 준비 상태 검증

**사용자 스토리:** 데이터베이스 관리자로서, 모든 전제 조건이 충족되었는지 검증하여, Grid Infrastructure 설치를 자신 있게 진행할 수 있도록 하고 싶습니다.

#### 인수 기준

1. WHEN 모든 구성 작업이 완료되면, THE RAC_System SHALL 모든 네트워크 인터페이스가 올바르게 구성되었는지 검증한다
2. WHEN 모든 구성 작업이 완료되면, THE RAC_System SHALL 필요한 모든 호스트 이름에 대해 DNS 해석이 작동하는지 검증한다
3. WHEN 모든 구성 작업이 완료되면, THE RAC_System SHALL grid 및 oracle 사용자를 위한 SSH User_Equivalence가 작동하는지 검증한다
4. WHEN 모든 구성 작업이 완료되면, THE RAC_System SHALL 두 노드에서 공유 스토리지에 접근 가능한지 검증한다
5. WHEN 모든 구성 작업이 완료되면, THE RAC_System SHALL 필요한 모든 OS 패키지가 설치되었는지 검증한다
6. WHEN 모든 구성 작업이 완료되면, THE RAC_System SHALL 커널 매개변수가 올바르게 설정되었는지 검증한다
7. WHEN 모든 구성 작업이 완료되면, THE RAC_System SHALL 시간 동기화가 작동하는지 검증한다
8. WHEN 모든 구성 작업이 완료되면, THE RAC_System SHALL systemd 및 cgroup v2 설정이 올바른지 검증한다
9. WHEN 모든 검증 확인이 통과하면, THE RAC_System SHALL 준비 완료 확인 메시지를 표시한다
10. IF 검증 확인이 실패하면, THEN THE RAC_System SHALL 문제 해결을 위한 상세한 오류 정보를 표시한다
