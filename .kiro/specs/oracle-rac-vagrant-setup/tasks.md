# 구현 계획: Oracle RAC Vagrant Setup

## 개요

본 구현 계획은 Oracle 19c RAC 2노드 클러스터를 로컬 개발 환경에서 자동으로 배포하는 시스템을 구축합니다. Vagrant를 통한 VM 프로비저닝과 Ansible을 통한 OS 레벨 구성 자동화를 포함하며, Infrastructure as Code 원칙을 따릅니다.

## 작업 목록

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
  
  - [x] 2.3 Vagrantfile 검증 테스트 작성
    - VM 구성 일관성 검증 (Property 1)
    - 공유 스토리지 접근성 검증 (Property 2)
    - VM 실행 상태 검증 (Property 3)
    - 프로비저닝 멱등성 검증 (Property 4)
    - 네트워크 어댑터 구성 검증 (Property 5)
    - _요구사항: 1.6, 1.7, 2.8_

- [ ] 3. DNS 및 /etc/hosts 구성
  - [x] 3.1 dnsmasq 설치 및 구성 스크립트 작성
    - node2에 dnsmasq 설치
    - SCAN 이름 해석 구성 (rac-scan.localdomain → 192.168.1.121-123)
    - VIP 및 호스트 이름 해석 구성
    - dnsmasq 서비스 활성화 및 시작
    - _요구사항: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_
  
  - [x] 3.2 /etc/hosts 파일 구성
    - 모든 노드에 호스트 이름 및 IP 매핑 추가
    - Public 및 Private 네트워크 호스트 이름 포함
    - _요구사항: 3.6, 3.7, 3.8, 3.9_
  
  - [x] 3.3 DNS 구성 검증 테스트 작성
    - DNS 서비스 가용성 검증 (Property 7)
    - DNS 라운드 로빈 검증 (Property 8)
    - DNS 해석 정확성 검증 (Property 9)
    - _요구사항: 3.10_

- [ ] 4. Ansible 인벤토리 및 기본 구조 생성
  - [~] 4.1 Ansible 인벤토리 파일 작성 (ansible/hosts.ini)
    - rac_nodes 그룹 정의 (node1, node2)
    - 연결 변수 설정 (ansible_user, ansible_host)
    - _요구사항: 12.1, 12.2, 12.3, 12.4_
  
  - [~] 4.2 Ansible 변수 파일 작성 (ansible/group_vars/rac_nodes.yml)
    - Oracle 그룹/사용자 정의 (UID/GID)
    - 디렉토리 경로 정의
    - 커널 매개변수 정의
    - systemd 설정 정의
    - _요구사항: 4.1-4.13, 10.1-10.9, 11.1-11.5_

- [ ] 5. Ansible Playbook - Oracle 사용자 및 그룹 구성
  - [~] 5.1 Oracle 그룹 생성 태스크 작성
    - oinstall, dba, asmdba, asmoper, asmadmin 그룹 생성
    - 지정된 GID 사용
    - _요구사항: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [~] 5.2 Oracle 사용자 생성 태스크 작성
    - grid 및 oracle 사용자 생성
    - 지정된 UID 및 그룹 멤버십 설정
    - _요구사항: 4.6, 4.7, 4.8, 4.9_
  
  - [~] 5.3 Oracle 디렉토리 생성 태스크 작성
    - /u01/app/grid, /u01/app/19.3.0/grid 생성 (소유자: grid)
    - /u01/app/oracle, /u01/app/oracle/product/19.3.0/dbhome_1 생성 (소유자: oracle)
    - 올바른 권한 및 소유권 설정
    - _요구사항: 4.10, 4.11, 4.12, 4.13_
  
  - [~] 5.4 사용자/그룹 구성 검증 테스트 작성
    - Oracle 그룹 구성 검증 (Property 10)
    - Oracle 사용자 구성 검증 (Property 11)
    - Oracle 디렉토리 구조 검증 (Property 12)

- [ ] 6. Ansible Playbook - 패키지 설치 및 OS 구성
  - [~] 6.1 Oracle Preinstall 패키지 설치 태스크 작성
    - oracle-database-preinstall-19c 패키지 설치
    - 필요한 추가 RPM 패키지 설치
    - _요구사항: 5.1, 5.4_
  
  - [~] 6.2 커널 매개변수 구성 태스크 작성
    - sysctl을 통한 커널 매개변수 설정 (shmmax, shmall, shmmni, file-max, ip_local_port_range)
    - /etc/sysctl.conf 파일 업데이트
    - _요구사항: 5.2, 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [~] 6.3 리소스 제한 구성 태스크 작성
    - /etc/security/limits.conf 파일 업데이트
    - grid 및 oracle 사용자의 nofile, nproc 제한 설정
    - _요구사항: 5.3, 10.6, 10.7, 10.8, 10.9_
  
  - [~] 6.4 패키지 및 OS 구성 검증 테스트 작성
    - Oracle Preinstall 패키지 설치 검증 (Property 13)
    - 커널 매개변수 검증 (Property 14)
    - 리소스 제한 검증 (Property 15)
    - 구성 지속성 검증 (Property 29)
    - _요구사항: 10.10_

- [~] 7. Checkpoint - 기본 구성 검증
  - 모든 테스트가 통과하는지 확인
  - 사용자에게 진행 상황 보고 및 질문 확인

- [ ] 8. Ansible Playbook - 보안 구성
  - [~] 8.1 방화벽 비활성화 태스크 작성
    - firewalld 서비스 중지 및 비활성화
    - _요구사항: 6.1_
  
  - [~] 8.2 SELinux 구성 태스크 작성
    - SELinux를 permissive 모드로 설정
    - /etc/selinux/config 파일 업데이트 (재부팅 후 유지)
    - _요구사항: 6.2, 6.3_
  
  - [~] 8.3 SSH 구성 태스크 작성
    - root 로그인 허용 설정
    - SSH 서비스 재시작
    - _요구사항: 6.4_
  
  - [~] 8.4 보안 구성 검증 테스트 작성
    - 방화벽 비활성화 검증 (Property 16)
    - SELinux Permissive 모드 검증 (Property 17)
    - SSH Root 로그인 허용 검증 (Property 18)

- [ ] 9. Ansible Playbook - SSH User Equivalence 구성
  - [~] 9.1 SSH 키 생성 태스크 작성
    - grid 및 oracle 사용자를 위한 2048 bits SSH 키 쌍 생성
    - _요구사항: 7.1, 7.2_
  
  - [~] 9.2 SSH 공개 키 수집 및 배포 태스크 작성
    - 각 노드에서 공개 키 수집
    - authorized_keys 모듈을 사용하여 모든 노드에 배포
    - _요구사항: 7.3, 7.4_
  
  - [~] 9.3 SSH User Equivalence 검증 태스크 작성
    - grid 및 oracle 사용자의 양방향 SSH 접속 테스트
    - _요구사항: 7.6, 7.7, 7.8, 7.9_
  
  - [~] 9.4 SSH 구성 검증 테스트 작성
    - SSH 키 생성 검증 (Property 19)
    - SSH 공개 키 배포 검증 (Property 20)
    - SSH User Equivalence 멱등성 검증 (Property 21)
    - SSH 비밀번호 없는 인증 검증 (Property 22)
    - _요구사항: 7.5_

- [ ] 10. Ansible Playbook - 시간 동기화 구성
  - [~] 10.1 Chrony 설치 및 구성 태스크 작성
    - chrony 패키지 설치
    - /etc/chrony.conf 파일 구성 (동일한 NTP 서버 사용)
    - chrony 서비스 활성화 및 시작
    - _요구사항: 8.1, 8.2, 8.4_
  
  - [~] 10.2 시간 동기화 검증 테스트 작성
    - Chrony 설치 및 구성 검증 (Property 23)
    - 시간 동기화 검증 (Property 24)
    - _요구사항: 8.3_

- [ ] 11. Ansible Playbook - 공유 스토리지 구성
  - [~] 11.1 udev rules 생성 태스크 작성
    - /etc/udev/rules.d/99-oracle-asmdevices.rules 파일 생성
    - /dev/sdb, /dev/sdc, /dev/sdd에 대한 규칙 정의
    - 소유자 grid, 그룹 asmadmin, 권한 0660 설정
    - _요구사항: 9.7, 9.8, 9.9, 9.10_
  
  - [~] 11.2 udev rules 적용 및 검증 태스크 작성
    - udevadm control --reload-rules 실행
    - udevadm trigger 실행
    - 디스크 권한 및 소유권 검증
    - _요구사항: 9.11_
  
  - [~] 11.3 스토리지 구성 검증 테스트 작성
    - 스토리지 컨트롤러 구성 검증 (Property 25)
    - ASM 디스크 구성 검증 (Property 26)
    - udev Rules 구성 검증 (Property 27)
    - 디스크 장치 이름 일관성 검증 (Property 28)
    - _요구사항: 9.12_

- [ ] 12. Ansible Playbook - Systemd 및 Cgroup 구성
  - [~] 12.1 Systemd 리소스 제어 구성 태스크 작성
    - /etc/systemd/system.conf 파일 업데이트 (DefaultTasksMax, DefaultMemoryAccounting)
    - /etc/systemd/logind.conf 파일 업데이트 (RemoveIPC)
    - _요구사항: 11.1, 11.2, 11.3, 11.4_
  
  - [~] 12.2 OOM Killer 방지 구성 태스크 작성
    - cgroup v2 메모리 제어 설정
    - Oracle 프로세스 우선순위 설정
    - _요구사항: 11.5_
  
  - [~] 12.3 Systemd 구성 재로드 태스크 작성
    - systemctl daemon-reload 실행
    - 변경사항 적용 확인
    - _요구사항: 11.6_
  
  - [~] 12.4 Systemd 구성 검증 테스트 작성
    - Systemd 리소스 제어 구성 검증 (Property 30)
    - OOM Killer 방지 구성 검증 (Property 31)
    - Systemd 구성 재로드 검증 (Property 32)
    - Cgroup 호환성 검증 (Property 33)
    - _요구사항: 11.7_

- [~] 13. Checkpoint - 전체 구성 검증
  - 모든 테스트가 통과하는지 확인
  - 사용자에게 진행 상황 보고 및 질문 확인

- [ ] 14. 메인 Ansible Playbook 통합 (ansible/site.yml)
  - [~] 14.1 메인 플레이북 작성
    - 모든 역할 및 태스크 통합
    - 실행 순서 정의
    - 에러 처리 및 롤백 전략 구현
    - _요구사항: 12.5, 12.6, 12.7, 12.8_
  
  - [~] 14.2 Vagrantfile에 Ansible 프로비저너 통합
    - node2에서 Ansible 플레이북 자동 실행
    - 인벤토리 파일 경로 지정
    - _요구사항: 12.1, 12.3, 14.2_
  
  - [~] 14.3 Ansible 통합 검증 테스트 작성
    - Ansible 설치 및 인벤토리 구성 검증 (Property 34)
    - Ansible Control Node 구성 검증 (Property 35)
    - Ansible 동시 구성 적용 검증 (Property 36)
    - Ansible 중앙 집중식 구성 검증 (Property 37)

- [ ] 15. 검증 스크립트 작성
  - [~] 15.1 네트워크 검증 스크립트 작성 (tests/verify_network.sh)
    - 네트워크 인터페이스 구성 확인
    - 노드 간 연결성 테스트 (ping)
    - _요구사항: 15.1_
  
  - [~] 15.2 DNS 검증 스크립트 작성 (tests/verify_dns.sh)
    - 모든 호스트 이름 해석 테스트
    - SCAN 라운드 로빈 확인
    - _요구사항: 15.2_
  
  - [~] 15.3 SSH 검증 스크립트 작성 (tests/verify_ssh.sh)
    - grid 및 oracle 사용자 SSH User Equivalence 테스트
    - 양방향 접속 확인
    - _요구사항: 15.3_
  
  - [~] 15.4 스토리지 검증 스크립트 작성 (tests/verify_storage.sh)
    - 공유 디스크 접근 확인
    - 디스크 권한 및 소유권 확인
    - _요구사항: 15.4_
  
  - [~] 15.5 시스템 구성 검증 스크립트 작성 (tests/verify_system.sh)
    - 패키지 설치 확인
    - 커널 매개변수 확인
    - 시간 동기화 확인
    - systemd 설정 확인
    - _요구사항: 15.5, 15.6, 15.7, 15.8_
  
  - [~] 15.6 통합 검증 스크립트 작성 (tests/verify_all.sh)
    - 모든 검증 스크립트 실행
    - 결과 요약 및 보고
    - 준비 완료 확인 메시지 또는 에러 정보 표시
    - _요구사항: 15.9, 15.10_
  
  - [~] 15.7 설치 준비 상태 검증 테스트 작성
    - 설치 준비 상태 검증 (Property 41)

- [ ] 16. 문서화
  - [~] 16.1 사용 가이드 작성 (docs/USAGE.md)
    - 시스템 요구사항 (VirtualBox, Vagrant, 디스크 공간)
    - 설치 및 실행 방법
    - 검증 방법
    - _요구사항: 14.4_
  
  - [~] 16.2 Oracle 19.19 RU 적용 가이드 작성 (docs/ORACLE_RU.md)
    - Oracle 19.19+ RU 요구사항 설명
    - gridSetup.sh -applyRU 옵션 사용 방법
    - 버전 검증 방법
    - _요구사항: 13.1, 13.2, 13.3, 13.4_
  
  - [~] 16.3 트러블슈팅 가이드 작성 (docs/TROUBLESHOOTING.md)
    - 일반적인 문제 및 해결 방법
    - 에러 로그 확인 방법
    - 롤백 및 재시작 절차
    - _요구사항: 14.6_
  
  - [~] 16.4 아키텍처 문서 작성 (docs/ARCHITECTURE.md)
    - 시스템 구조 설명
    - 컴포넌트 간 상호작용
    - 네트워크 토폴로지
    - _요구사항: 14.4_

- [ ] 17. 최종 통합 테스트 및 검증
  - [~] 17.1 전체 배포 프로세스 테스트
    - vagrant up 실행
    - Ansible 플레이북 자동 실행 확인
    - 모든 검증 스크립트 실행
    - _요구사항: 14.2, 14.5_
  
  - [~] 17.2 멱등성 테스트
    - 동일한 구성으로 재실행
    - 결과 일관성 확인
    - _요구사항: 14.1, 14.5_
  
  - [~] 17.3 속성 기반 테스트 실행
    - 모든 정확성 속성 검증 (Property 1-41)
    - 최소 100회 반복 실행
  
  - [~] 17.4 Oracle 버전 검증 테스트
    - Oracle 버전 검증 (Property 38)
    - 완전 자동화 검증 (Property 39)
    - Silent 모드 설치 검증 (Property 40)
    - _요구사항: 13.3, 14.3_

- [~] 18. 최종 Checkpoint - 배포 완료 확인
  - 모든 테스트가 통과하는지 확인
  - 문서가 완성되었는지 확인
  - 사용자에게 최종 결과 보고

## 참고사항

- `*` 표시가 있는 작업은 선택 사항이며, 빠른 MVP를 위해 건너뛸 수 있습니다
- 각 작업은 특정 요구사항을 참조하여 추적 가능성을 보장합니다
- Checkpoint 작업은 점진적 검증을 보장합니다
- 속성 기반 테스트는 보편적 정확성 속성을 검증합니다
- 단위 테스트는 특정 예제 및 엣지 케이스를 검증합니다
- 모든 구성은 멱등성을 보장하여 반복 실행 시 동일한 결과를 생성합니다
