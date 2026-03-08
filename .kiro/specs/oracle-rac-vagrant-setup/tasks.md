# 구현 계획: Oracle RAC Vagrant Setup

## 개요

본 구현 계획은 Oracle 19c RAC 2노드 클러스터를 로컬 개발 환경에서 자동으로 배포하는 시스템을 구축합니다. Vagrant를 통한 VM 프로비저닝과 Ansible을 통한 OS 레벨 구성 자동화를 포함하며, Infrastructure as Code 원칙을 따릅니다.

## 배포 흐름

1. **Phase 1 - Host에서 실행 (OS 독립적)**:
   - Vagrantfile 작성 및 검증 (Python 기반 테스트)
   - `vagrant up` 실행으로 VM 프로비저닝
   - DNS 및 /etc/hosts 구성 (Vagrant provisioner)

2. **Phase 2 - node2에서 Ansible 실행 (Linux VM 내부)**:
   - node2가 Ansible control node로 동작
   - node1과 node2를 동시에 구성
   - 모든 OS 레벨 설정 자동화
   - 검증 및 준비 상태 확인

3. **Phase 3 - 검증 (Host에서 실행, OS 독립적)**:
   - Python 기반 property 테스트
   - `vagrant ssh` 명령으로 VM 내부 검증

## 작업 목록

### Phase 1: Host에서 실행 (OS 독립적)

- [x] 1. 프로젝트 구조 및 기본 파일 생성
  - 디렉토리 구조 생성 (ansible/, tests/, docs/)
  - README.md 작성 (프로젝트 개요, 사용 방법)
  - .gitignore 파일 생성 (VM 파일, 디스크 이미지 제외)
  - _요구사항: 14.4_

- [ ] 2. Vagrantfile 작성 - VM 프로비저닝
  - [x] 2.1 기본 Vagrantfile 구조 및 node1 VM 정의
    - rockylinux/9 베이스 이미지 설정
    - node1 호스트명, 네트워크 인터페이스 구성 (192.168.1.101, 10.0.0.101)
    - 리소스 할당 (8GB RAM, 2 CPU)
    - _요구사항: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.5, 2.7_
  
  - [x] 2.2 node2 VM 정의 및 공유 스토리지 구성
    - node2 호스트명, 네트워크 인터페이스 구성 (192.168.1.102, 10.0.0.102)
    - 리소스 할당 (8GB RAM, 2 CPU)
    - 공유 디스크 생성 (asm_disk1, asm_disk2, asm_disk3)
    - SATA Controller를 통한 공유 스토리지 연결 (Fixed, Shareable)
    - _요구사항: 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.4, 2.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [x] 2.3 Vagrantfile 검증 테스트 작성 (Python 기반, OS 독립적)
    - VM 구성 일관성 검증 (Property 1)
    - 공유 스토리지 접근성 검증 (Property 2)
    - VM 실행 상태 검증 (Property 3)
    - 프로비저닝 멱등성 검증 (Property 4)
    - 네트워크 어댑터 구성 검증 (Property 5)
    - _요구사항: 1.6, 1.7, 2.8_

- [x] 3. Vagrantfile에 Provisioner 통합
  - [x] 3.1 DNS 및 /etc/hosts 구성 스크립트를 Vagrant provisioner로 통합
    - scripts/setup_dnsmasq.sh를 node2 provisioner로 추가
    - scripts/setup_hosts.sh를 node1, node2 provisioner로 추가
    - Vagrant provisioner 순서 정의 (shell provisioner 먼저, ansible provisioner 나중)
    - _요구사항: 3.1-3.9_
  
  - [x] 3.2 Ansible provisioner 통합
    - node2를 Ansible control node로 설정
    - node2에서 ansible/site.yml 자동 실행 설정
    - Ansible 인벤토리 경로 지정
    - _요구사항: 12.1, 12.3, 14.2_
  
  - [x] 3.3 Vagrant provisioner 검증 테스트 작성 (Python 기반)
    - DNS 서비스 가용성 검증 (Property 7)
    - DNS 라운드 로빈 검증 (Property 8)
    - DNS 해석 정확성 검증 (Property 9)
    - _요구사항: 3.10_

- [x] 4. vagrant up 실행 가이드 작성
  - [x] 4.1 실행 전 체크리스트 문서화
    - VirtualBox 설치 확인
    - Vagrant 설치 확인
    - 디스크 공간 확인 (최소 60GB)
    - 메모리 확인 (최소 16GB)
    - _요구사항: 14.4_
  
  - [x] 4.2 vagrant up 실행 명령 및 예상 시간 문서화
    - 실행 명령: `vagrant up`
    - 예상 소요 시간: 15-20분
    - 진행 상황 모니터링 방법
    - _요구사항: 14.2, 14.5_

### Phase 2: node2에서 Ansible 실행 (VM 내부, 자동)

- [ ] 5. Ansible 인벤토리 및 기본 구조 (이미 완료)
  - [x] 5.1 Ansible 인벤토리 파일 작성 (ansible/hosts.ini)
    - rac_nodes 그룹 정의 (node1, node2)
    - 연결 변수 설정 (ansible_user, ansible_host)
    - _요구사항: 12.1, 12.2, 12.3, 12.4_
  
  - [x] 5.2 Ansible 변수 파일 작성 (ansible/group_vars/rac_nodes.yml)
    - Oracle 그룹/사용자 정의 (UID/GID)
    - 디렉토리 경로 정의
    - 커널 매개변수 정의
    - systemd 설정 정의
    - _요구사항: 4.1-4.13, 10.1-10.9, 11.1-11.5_

- [ ] 6. Ansible Playbook - Oracle 사용자 및 그룹 구성 (이미 완료)
  - [x] 6.1 Oracle 그룹 생성 태스크 작성
    - oinstall, dba, asmdba, asmoper, asmadmin 그룹 생성
    - 지정된 GID 사용
    - _요구사항: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 6.2 Oracle 사용자 생성 태스크 작성
    - grid 및 oracle 사용자 생성
    - 지정된 UID 및 그룹 멤버십 설정
    - _요구사항: 4.6, 4.7, 4.8, 4.9_
  
  - [x] 6.3 Oracle 디렉토리 생성 태스크 작성
    - /u01/app/grid, /u01/app/19.3.0/grid 생성 (소유자: grid)
    - /u01/app/oracle, /u01/app/oracle/product/19.3.0/dbhome_1 생성 (소유자: oracle)
    - 올바른 권한 및 소유권 설정
    - _요구사항: 4.10, 4.11, 4.12, 4.13_

- [ ] 7. Ansible Playbook - 패키지 설치 및 OS 구성 (이미 완료)
  - [x] 7.1 Oracle Preinstall 패키지 설치 태스크 작성
    - oracle-database-preinstall-19c 패키지 설치
    - 필요한 추가 RPM 패키지 설치
    - _요구사항: 5.1, 5.4_
  
  - [x] 7.2 커널 매개변수 구성 태스크 작성
    - sysctl을 통한 커널 매개변수 설정 (shmmax, shmall, shmmni, file-max, ip_local_port_range)
    - /etc/sysctl.conf 파일 업데이트
    - _요구사항: 5.2, 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [x] 7.3 리소스 제한 구성 태스크 작성
    - /etc/security/limits.conf 파일 업데이트
    - grid 및 oracle 사용자의 nofile, nproc 제한 설정
    - _요구사항: 5.3, 10.6, 10.7, 10.8, 10.9_


- [ ] 8. Ansible Playbook - 보안 구성
  - [ ] 8.1 방화벽 비활성화 태스크 작성
    - firewalld 서비스 중지 및 비활성화
    - _요구사항: 6.1_
  
  - [ ] 8.2 SELinux 구성 태스크 작성
    - SELinux를 permissive 모드로 설정
    - /etc/selinux/config 파일 업데이트 (재부팅 후 유지)
    - _요구사항: 6.2, 6.3_
  
  - [ ] 8.3 SSH 구성 태스크 작성
    - root 로그인 허용 설정
    - SSH 서비스 재시작
    - _요구사항: 6.4_

- [ ] 9. Ansible Playbook - SSH User Equivalence 구성
  - [ ] 9.1 SSH 키 생성 태스크 작성
    - grid 및 oracle 사용자를 위한 2048 bits SSH 키 쌍 생성
    - _요구사항: 7.1, 7.2_
  
  - [ ] 9.2 SSH 공개 키 수집 및 배포 태스크 작성
    - 각 노드에서 공개 키 수집
    - authorized_keys 모듈을 사용하여 모든 노드에 배포
    - _요구사항: 7.3, 7.4_
  
  - [ ] 9.3 SSH User Equivalence 검증 태스크 작성
    - grid 및 oracle 사용자의 양방향 SSH 접속 테스트
    - _요구사항: 7.6, 7.7, 7.8, 7.9_

- [ ] 10. Ansible Playbook - 시간 동기화 구성
  - [ ] 10.1 Chrony 설치 및 구성 태스크 작성
    - chrony 패키지 설치
    - /etc/chrony.conf 파일 구성 (동일한 NTP 서버 사용)
    - chrony 서비스 활성화 및 시작
    - _요구사항: 8.1, 8.2, 8.4_

- [ ] 11. Ansible Playbook - 공유 스토리지 구성
  - [ ] 11.1 udev rules 생성 태스크 작성
    - /etc/udev/rules.d/99-oracle-asmdevices.rules 파일 생성
    - /dev/sdb, /dev/sdc, /dev/sdd에 대한 규칙 정의
    - 소유자 grid, 그룹 asmadmin, 권한 0660 설정
    - _요구사항: 9.7, 9.8, 9.9, 9.10_
  
  - [ ] 11.2 udev rules 적용 및 검증 태스크 작성
    - udevadm control --reload-rules 실행
    - udevadm trigger 실행
    - 디스크 권한 및 소유권 검증
    - _요구사항: 9.11_

- [ ] 12. Ansible Playbook - Systemd 및 Cgroup 구성
  - [ ] 12.1 Systemd 리소스 제어 구성 태스크 작성
    - /etc/systemd/system.conf 파일 업데이트 (DefaultTasksMax, DefaultMemoryAccounting)
    - /etc/systemd/logind.conf 파일 업데이트 (RemoveIPC)
    - _요구사항: 11.1, 11.2, 11.3, 11.4_
  
  - [ ] 12.2 OOM Killer 방지 구성 태스크 작성
    - cgroup v2 메모리 제어 설정
    - Oracle 프로세스 우선순위 설정
    - _요구사항: 11.5_
  
  - [ ] 12.3 Systemd 구성 재로드 태스크 작성
    - systemctl daemon-reload 실행
    - 변경사항 적용 확인
    - _요구사항: 11.6_

- [ ] 13. 메인 Ansible Playbook 통합 (ansible/site.yml)
  - [ ] 13.1 메인 플레이북 작성
    - 모든 역할 및 태스크 통합
    - 실행 순서 정의 (사용자/그룹 → 패키지 → 보안 → SSH → 시간 → 스토리지 → systemd)
    - 에러 처리 및 롤백 전략 구현
    - _요구사항: 12.5, 12.6, 12.7, 12.8_
  
  - [ ] 13.2 Ansible 실행 환경 준비 스크립트 작성
    - node2에 Ansible 설치 스크립트
    - SSH 키 생성 및 배포 (root 사용자)
    - Ansible 인벤토리 및 변수 파일 복사
    - _요구사항: 12.1, 12.3_

### Phase 3: Host에서 검증 (OS 독립적, Python 기반)

- [ ] 14. Property-Based 테스트 작성 (Python, vagrant ssh 사용)
  - [ ] 14.1 보안 구성 검증 테스트
    - 방화벽 비활성화 검증 (Property 16)
    - SELinux Permissive 모드 검증 (Property 17)
    - SSH Root 로그인 허용 검증 (Property 18)
    - _요구사항: 6.1, 6.2, 6.3, 6.4_
  
  - [ ] 14.2 SSH User Equivalence 검증 테스트
    - SSH 키 생성 검증 (Property 19)
    - SSH 공개 키 배포 검증 (Property 20)
    - SSH User Equivalence 멱등성 검증 (Property 21)
    - SSH 비밀번호 없는 인증 검증 (Property 22)
    - _요구사항: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ] 14.3 시간 동기화 검증 테스트
    - Chrony 설치 및 구성 검증 (Property 23)
    - 시간 동기화 검증 (Property 24)
    - _요구사항: 8.1, 8.2, 8.3, 8.4_
  
  - [ ] 14.4 스토리지 구성 검증 테스트
    - 스토리지 컨트롤러 구성 검증 (Property 25)
    - ASM 디스크 구성 검증 (Property 26)
    - udev Rules 구성 검증 (Property 27)
    - 디스크 장치 이름 일관성 검증 (Property 28)
    - _요구사항: 9.1-9.12_
  
  - [ ] 14.5 Systemd 구성 검증 테스트
    - Systemd 리소스 제어 구성 검증 (Property 30)
    - OOM Killer 방지 구성 검증 (Property 31)
    - Systemd 구성 재로드 검증 (Property 32)
    - Cgroup 호환성 검증 (Property 33)
    - _요구사항: 11.1-11.7_
  
  - [ ] 14.6 Ansible 통합 검증 테스트
    - Ansible 설치 및 인벤토리 구성 검증 (Property 34)
    - Ansible Control Node 구성 검증 (Property 35)
    - Ansible 동시 구성 적용 검증 (Property 36)
    - Ansible 중앙 집중식 구성 검증 (Property 37)
    - _요구사항: 12.1-12.8_
  
  - [ ] 14.7 설치 준비 상태 검증 테스트
    - 설치 준비 상태 검증 (Property 41)
    - _요구사항: 15.1-15.10_

- [ ] 15. 검증 스크립트 작성 (Bash, VM 내부 실행)
  - [ ] 15.1 네트워크 검증 스크립트 작성 (tests/verify_network.sh)
    - 네트워크 인터페이스 구성 확인
    - 노드 간 연결성 테스트 (ping)
    - _요구사항: 15.1_
  
  - [ ] 15.2 DNS 검증 스크립트 작성 (tests/verify_dns.sh)
    - 모든 호스트 이름 해석 테스트
    - SCAN 라운드 로빈 확인
    - _요구사항: 15.2_
  
  - [ ] 15.3 SSH 검증 스크립트 작성 (tests/verify_ssh.sh)
    - grid 및 oracle 사용자 SSH User Equivalence 테스트
    - 양방향 접속 확인
    - _요구사항: 15.3_
  
  - [ ] 15.4 스토리지 검증 스크립트 작성 (tests/verify_storage.sh)
    - 공유 디스크 접근 확인
    - 디스크 권한 및 소유권 확인
    - _요구사항: 15.4_
  
  - [ ] 15.5 시스템 구성 검증 스크립트 작성 (tests/verify_system.sh)
    - 패키지 설치 확인
    - 커널 매개변수 확인
    - 시간 동기화 확인
    - systemd 설정 확인
    - _요구사항: 15.5, 15.6, 15.7, 15.8_
  
  - [ ] 15.6 통합 검증 스크립트 작성 (tests/verify_all.sh)
    - 모든 검증 스크립트 실행
    - 결과 요약 및 보고
    - 준비 완료 확인 메시지 또는 에러 정보 표시
    - _요구사항: 15.9, 15.10_

### Phase 4: 문서화 및 최종 검증

- [ ] 16. 문서화
  - [ ] 16.1 사용 가이드 작성 (docs/USAGE.md)
    - 시스템 요구사항 (VirtualBox, Vagrant, 디스크 공간)
    - 설치 및 실행 방법 (vagrant up 한 번만 실행)
    - 검증 방법 (Python 테스트 실행)
    - _요구사항: 14.4_
  
  - [ ] 16.2 Oracle 19.19 RU 적용 가이드 작성 (docs/ORACLE_RU.md)
    - Oracle 19.19+ RU 요구사항 설명
    - gridSetup.sh -applyRU 옵션 사용 방법
    - 버전 검증 방법
    - _요구사항: 13.1, 13.2, 13.3, 13.4_
  
  - [ ] 16.3 트러블슈팅 가이드 작성 (docs/TROUBLESHOOTING.md)
    - 일반적인 문제 및 해결 방법
    - 에러 로그 확인 방법
    - 롤백 및 재시작 절차 (vagrant destroy && vagrant up)
    - _요구사항: 14.6_
  
  - [ ] 16.4 아키텍처 문서 작성 (docs/ARCHITECTURE.md)
    - 시스템 구조 설명
    - 컴포넌트 간 상호작용
    - 네트워크 토폴로지
    - Phase별 실행 흐름
    - _요구사항: 14.4_

- [ ] 17. 최종 통합 테스트 및 검증
  - [ ] 17.1 전체 배포 프로세스 테스트 (Host에서 실행)
    - vagrant destroy -f (기존 VM 삭제)
    - vagrant up (전체 프로비저닝)
    - Python 테스트 실행 (모든 Property 검증)
    - _요구사항: 14.2, 14.5_
  
  - [ ] 17.2 멱등성 테스트
    - vagrant provision 재실행
    - 결과 일관성 확인
    - _요구사항: 14.1, 14.5_
  
  - [ ] 17.3 속성 기반 테스트 실행 (Host에서 실행)
    - 모든 정확성 속성 검증 (Property 1-41)
    - 최소 100회 반복 실행
    - pytest 명령으로 실행
  
  - [ ] 17.4 Oracle 버전 검증 테스트
    - Oracle 버전 검증 (Property 38)
    - 완전 자동화 검증 (Property 39)
    - Silent 모드 설치 검증 (Property 40)
    - _요구사항: 13.3, 14.3_

- [ ] 18. 최종 Checkpoint - 배포 완료 확인
  - 모든 테스트가 통과하는지 확인
  - 문서가 완성되었는지 확인
  - 사용자에게 최종 결과 보고
  - Git 커밋 및 푸시


## 참고사항

### 실행 흐름 요약

```
Host (Windows/Linux/Mac)
  │
  ├─ Phase 1: Vagrantfile 작성 및 검증 (Python 테스트)
  │
  ├─ vagrant up 실행
  │   │
  │   ├─ VirtualBox: node1, node2 VM 생성
  │   ├─ Shell Provisioner: DNS 및 /etc/hosts 구성
  │   └─ Ansible Provisioner: node2에서 site.yml 실행
  │       │
  │       └─ node2 (Ansible Control Node)
  │           │
  │           ├─ node1 구성 (SSH를 통해)
  │           │   ├─ 사용자/그룹 생성
  │           │   ├─ 패키지 설치
  │           │   ├─ 보안 설정
  │           │   ├─ SSH User Equivalence
  │           │   ├─ 시간 동기화
  │           │   ├─ 스토리지 구성
  │           │   └─ Systemd 설정
  │           │
  │           └─ node2 구성 (localhost)
  │               ├─ 사용자/그룹 생성
  │               ├─ 패키지 설치
  │               ├─ 보안 설정
  │               ├─ SSH User Equivalence
  │               ├─ 시간 동기화
  │               ├─ 스토리지 구성
  │               └─ Systemd 설정
  │
  └─ Phase 3: 검증 (Python 테스트, vagrant ssh 사용)
      ├─ Property-Based Tests (100회 반복)
      └─ Bash 검증 스크립트 (VM 내부)
```

### OS 독립성 보장

- **Host 작업**: Python 기반 테스트, vagrant 명령만 사용
- **VM 작업**: Bash 스크립트, Ansible playbook (Linux 환경)
- **통신**: `vagrant ssh` 명령으로 Host ↔ VM 통신
- **파일 공유**: Vagrant synced folder 사용 (자동 처리)

### 주요 변경사항

1. **DNS 구성**: Vagrant shell provisioner로 이동 (vagrant up 시 자동 실행)
2. **Ansible 실행**: Vagrant ansible provisioner로 통합 (vagrant up 시 자동 실행)
3. **테스트**: 모두 Python 기반으로 통일, `vagrant ssh` 명령 사용
4. **검증 스크립트**: Bash로 작성, VM 내부에서 실행

### 작업 순서

1. Task 3: Vagrantfile에 provisioner 통합
2. Task 4: vagrant up 실행 가이드 작성
3. Task 5-13: Ansible playbook 작성 (node2에서 자동 실행)
4. Task 14-15: Python 테스트 및 Bash 검증 스크립트 작성
5. Task 16-18: 문서화 및 최종 검증

### 멱등성 보장

- 모든 Ansible 작업은 멱등성 보장
- `vagrant provision` 재실행 가능
- `vagrant destroy && vagrant up` 으로 완전 재시작 가능

### 테스트 실행 방법

```bash
# Host에서 실행 (OS 독립적)
pytest tests/ --hypothesis-profile=ci

# 특정 Property 테스트
pytest tests/test_vagrantfile_properties.py -v

# VM 내부 검증 스크립트 실행
vagrant ssh node2 -c "bash /vagrant/tests/verify_all.sh"
```
