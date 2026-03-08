# Oracle RAC Vagrant Setup - Property-Based Tests

이 디렉토리는 Oracle 19c RAC 2-Node Cluster Vagrant 설정에 대한 속성 기반 테스트(Property-Based Tests)를 포함합니다.

## 테스트 개요

### 테스트 유형

1. **속성 기반 테스트 (Property-Based Tests)**
   - 모든 입력에 대한 보편적 속성 검증
   - 최소 100회 반복 실행
   - Hypothesis 프레임워크 사용

2. **단위 테스트 (Unit Tests)**
   - 특정 예제 및 엣지 케이스 검증
   - 구성 파일 존재 여부 확인
   - 리소스 할당 검증

### 테스트 속성 (Properties)

#### Property 1: VM 구성 일관성
- **검증 요구사항**: 1.1, 1.2, 1.3, 1.4
- **설명**: 모든 VM이 rockylinux/9 베이스 이미지, 8GB RAM, 최소 2 CPU 코어, 2개의 네트워크 어댑터를 가져야 함

#### Property 2: 공유 스토리지 접근성
- **검증 요구사항**: 1.5, 9.12
- **설명**: 모든 RAC 노드가 공유 스토리지 장치(/dev/sdb, /dev/sdc, /dev/sdd)에 접근 가능해야 함

#### Property 3: VM 실행 상태
- **검증 요구사항**: 1.6
- **설명**: 프로비저닝 완료 후 두 VM(node1, node2)이 모두 실행 상태여야 함

#### Property 4: 프로비저닝 멱등성
- **검증 요구사항**: 1.7, 14.1, 14.5
- **설명**: 동일한 Vagrantfile로 여러 번 프로비저닝 시 동일한 결과 생성

#### Property 5: 네트워크 어댑터 구성
- **검증 요구사항**: 2.1, 2.2, 2.7
- **설명**: Adapter 1은 private_network 타입, Adapter 2는 virtualbox__intnet 옵션 사용

#### Property 7: DNS 서비스 가용성
- **검증 요구사항**: 3.1
- **설명**: 모든 RAC 클러스터에 대해 최소 한 노드에 dnsmasq가 설치되고 실행 중이어야 함

#### Property 8: DNS 라운드 로빈
- **검증 요구사항**: 3.3
- **설명**: SCAN 이름(rac-scan.localdomain) 조회 시 세 개의 IP 주소(192.168.1.121, 192.168.1.122, 192.168.1.123) 중 하나가 반환되어야 함

#### Property 9: DNS 해석 정확성
- **검증 요구사항**: 3.10
- **설명**: 모든 구성된 호스트 이름에 대해 DNS 조회가 올바른 IP 주소를 반환해야 함

#### Property 10: Oracle 그룹 구성
- **검증 요구사항**: 4.1, 4.2, 4.3, 4.4, 4.5
- **설명**: 모든 RAC 노드에 대해 Oracle 그룹들(oinstall, dba, asmdba, asmoper, asmadmin)이 지정된 GID로 존재해야 함

#### Property 11: Oracle 사용자 구성
- **검증 요구사항**: 4.6, 4.7, 4.8, 4.9
- **설명**: 모든 RAC 노드에 대해 grid 사용자(UID 54331)와 oracle 사용자(UID 54321)가 기본 그룹 oinstall로 존재하고 올바른 보조 그룹에 속해야 함

#### Property 12: Oracle 디렉토리 구조
- **검증 요구사항**: 4.10, 4.11, 4.12, 4.13
- **설명**: 모든 RAC 노드에 대해 필요한 모든 Oracle 디렉토리가 올바른 소유자와 그룹으로 존재해야 함

## 사전 요구사항

### 필수 소프트웨어

1. **Python 3.8 이상**
   ```bash
   python --version
   ```

2. **VirtualBox**
   ```bash
   VBoxManage --version
   ```

3. **Vagrant**
   ```bash
   vagrant --version
   ```

### Python 패키지 설치

```bash
# 테스트 디렉토리로 이동
cd tests

# 의존성 설치
pip install -r requirements.txt
```

## 테스트 실행

### 전체 테스트 실행

```bash
# Vagrantfile 속성 테스트
pytest tests/test_vagrantfile_properties.py -v

# DNS 구성 속성 테스트
pytest tests/test_dns_properties.py -v

# 모든 테스트 실행
pytest tests/ -v
```

### 특정 속성 테스트 실행

```bash
# Vagrantfile 테스트
# Property 1만 실행
pytest tests/test_vagrantfile_properties.py::test_property_1_vm_configuration_consistency -v

# Property 2만 실행
pytest tests/test_vagrantfile_properties.py::test_property_2_shared_storage_accessibility -v

# DNS 테스트
# Property 7만 실행 (DNS 서비스 가용성)
pytest tests/test_dns_properties.py::test_property_7_dns_service_availability -v

# Property 8만 실행 (DNS 라운드 로빈)
pytest tests/test_dns_properties.py::test_property_8_dns_round_robin -v

# Property 9만 실행 (DNS 해석 정확성)
pytest tests/test_dns_properties.py::test_property_9_dns_resolution_accuracy -v
```

### 상세 출력과 함께 실행

```bash
pytest tests/test_vagrantfile_properties.py -v --tb=short
```

### 커버리지 리포트와 함께 실행

```bash
pytest tests/test_vagrantfile_properties.py --cov=. --cov-report=html
```

## 테스트 시나리오

### 시나리오 1: Vagrantfile 구문 검증 (VM 없이)

이 테스트들은 VM을 프로비저닝하지 않고도 실행 가능합니다:

```bash
pytest tests/test_vagrantfile_properties.py::test_vagrantfile_exists -v
pytest tests/test_vagrantfile_properties.py::test_property_1_vm_configuration_consistency -v
pytest tests/test_vagrantfile_properties.py::test_property_4_provisioning_idempotence -v
pytest tests/test_vagrantfile_properties.py::test_property_5_network_adapter_configuration -v
```

### 시나리오 2: 실행 중인 VM 검증

이 테스트들은 VM이 실행 중이어야 합니다:

```bash
# 먼저 VM 프로비저닝
vagrant up

# Vagrantfile 테스트 - 실행 상태 및 스토리지 접근성
pytest tests/test_vagrantfile_properties.py::test_property_3_vm_running_state -v
pytest tests/test_vagrantfile_properties.py::test_property_2_shared_storage_accessibility -v
```

### 시나리오 3: DNS 구성 검증

이 테스트들은 VM이 실행 중이고 DNS가 구성되어 있어야 합니다:

```bash
# 먼저 VM 프로비저닝 및 DNS 설정
vagrant up
vagrant ssh node2 -c "sudo bash /vagrant/scripts/setup_dnsmasq.sh"

# DNS 속성 테스트 실행
pytest tests/test_dns_properties.py::test_property_7_dns_service_availability -v
pytest tests/test_dns_properties.py::test_property_8_dns_round_robin -v
pytest tests/test_dns_properties.py::test_property_9_dns_resolution_accuracy -v

# 모든 DNS 테스트 실행
pytest tests/test_dns_properties.py -v
```

### 시나리오 4: 전체 통합 테스트

```bash
# VM 프로비저닝 및 DNS 설정
vagrant up
vagrant ssh node2 -c "sudo bash /vagrant/scripts/setup_dnsmasq.sh"

# 모든 테스트 실행
pytest tests/ -v
```

### 시나리오 5: Oracle 사용자/그룹/디렉토리 검증

이 테스트들은 VM이 실행 중이고 Ansible 플레이북이 실행되어야 합니다:

```bash
# 먼저 VM 프로비저닝
vagrant up

# Ansible 플레이북 실행 (node2에서)
vagrant ssh node2 -c "cd /vagrant/ansible && ansible-playbook -i hosts.ini playbooks/01_oracle_users_groups.yml"

# Oracle 사용자/그룹/디렉토리 속성 테스트 실행
pytest tests/test_oracle_users_groups_properties.py -v

# 또는 편리한 스크립트 사용
# Linux/Mac
bash tests/run_users_groups_tests.sh

# Windows
tests\run_users_groups_tests.bat
```

## 테스트 결과 해석

### 성공 예시

```
# Vagrantfile 테스트
tests/test_vagrantfile_properties.py::test_property_1_vm_configuration_consistency PASSED
tests/test_vagrantfile_properties.py::test_property_2_shared_storage_accessibility PASSED
tests/test_vagrantfile_properties.py::test_property_3_vm_running_state PASSED
tests/test_vagrantfile_properties.py::test_property_4_provisioning_idempotence PASSED
tests/test_vagrantfile_properties.py::test_property_5_network_adapter_configuration PASSED

# DNS 테스트
tests/test_dns_properties.py::test_property_7_dns_service_availability PASSED
tests/test_dns_properties.py::test_property_8_dns_round_robin PASSED
tests/test_dns_properties.py::test_property_9_dns_resolution_accuracy PASSED

# Oracle 사용자/그룹/디렉토리 테스트
tests/test_oracle_users_groups_properties.py::test_property_10_oracle_groups_configuration PASSED
tests/test_oracle_users_groups_properties.py::test_property_11_oracle_users_configuration PASSED
tests/test_oracle_users_groups_properties.py::test_property_12_oracle_directory_structure PASSED
```

### 실패 예시

```
# Vagrantfile 테스트 실패
FAILED tests/test_vagrantfile_properties.py::test_property_1_vm_configuration_consistency
AssertionError: node1 should have 8192MB RAM, got 4096MB

# DNS 테스트 실패
FAILED tests/test_dns_properties.py::test_property_9_dns_resolution_accuracy
AssertionError: Hostname node1.localdomain should resolve to 192.168.1.101, got []

# Oracle 사용자/그룹 테스트 실패
FAILED tests/test_oracle_users_groups_properties.py::test_property_10_oracle_groups_configuration
AssertionError: Group oinstall has GID 1001, expected 54321 on node1
```

## 문제 해결

### VM이 실행되지 않음

```bash
# VM 상태 확인
vagrant status

# VM 시작
vagrant up

# VM 재시작
vagrant reload
```

### VBoxManage 명령을 찾을 수 없음

VirtualBox가 설치되어 있고 PATH에 추가되어 있는지 확인:

```bash
# Windows
set PATH=%PATH%;C:\Program Files\Oracle\VirtualBox

# Linux/Mac
export PATH=$PATH:/usr/local/bin
```

### 테스트 스킵됨

일부 테스트는 VM이 실행 중이지 않거나 DNS가 구성되지 않으면 자동으로 스킵됩니다:

```
# VM이 실행 중이지 않을 때
SKIPPED [1] tests/test_vagrantfile_properties.py:123: VM node1 is not running

# DNS가 구성되지 않았을 때
SKIPPED [1] tests/test_dns_properties.py:234: dnsmasq is not running on node2. Run setup_dnsmasq.sh first.

# Ansible 플레이북이 실행되지 않았을 때
SKIPPED [1] tests/test_oracle_users_groups_properties.py:123: Oracle groups not configured. Run Ansible playbook first.
```

이는 정상적인 동작이며, 필요한 설정을 완료한 후 다시 테스트하세요:

```bash
# VM 시작
vagrant up

# DNS 설정
vagrant ssh node2 -c "sudo bash /vagrant/scripts/setup_dnsmasq.sh"

# Oracle 사용자/그룹 설정
vagrant ssh node2 -c "cd /vagrant/ansible && ansible-playbook -i hosts.ini playbooks/01_oracle_users_groups.yml"
```

## CI/CD 통합

### GitHub Actions 예시

```yaml
name: Vagrantfile Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
      
      - name: Run static tests (no VM required)
        run: |
          pytest tests/test_vagrantfile_properties.py \
            -k "not property_2 and not property_3" \
            -v
      
      - name: Run DNS configuration tests (requires VM)
        run: |
          # Note: This would require VM provisioning in CI
          # For now, we only run static tests
          echo "DNS tests require running VMs - skipped in CI"
```

## 테스트 파일 구조

### test_vagrantfile_properties.py
Vagrantfile 구성 검증을 위한 속성 기반 테스트:
- Property 1: VM 구성 일관성
- Property 2: 공유 스토리지 접근성
- Property 3: VM 실행 상태
- Property 4: 프로비저닝 멱등성
- Property 5: 네트워크 어댑터 구성

### test_dns_properties.py
DNS 구성 검증을 위한 속성 기반 테스트:
- Property 7: DNS 서비스 가용성
- Property 8: DNS 라운드 로빈
- Property 9: DNS 해석 정확성

### test_oracle_users_groups_properties.py
Oracle 사용자, 그룹, 디렉토리 구성 검증을 위한 속성 기반 테스트:
- Property 10: Oracle 그룹 구성
- Property 11: Oracle 사용자 구성
- Property 12: Oracle 디렉토리 구조

각 테스트 파일은 다음을 포함합니다:
- 속성 기반 테스트 (최소 100회 반복)
- 단위 테스트 (특정 예제 및 엣지 케이스)
- 헬퍼 함수 (VM 상태 확인, 명령 실행 등)

## 추가 정보

- **최소 반복 횟수**: 각 속성 테스트는 최소 100회 반복 실행됩니다
- **테스트 프레임워크**: Python Hypothesis
- **테스트 태그 형식**: `Feature: oracle-rac-vagrant-setup, Property {number}: {property_text}`

## 참고 문서

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Vagrant Documentation](https://www.vagrantup.com/docs)
- [VirtualBox Documentation](https://www.virtualbox.org/manual/)


## 검증 스크립트

### verify_hosts.sh

**목적**: /etc/hosts 파일 구성을 검증합니다.

**요구사항**: 3.6, 3.7, 3.8, 3.9

**기능**:
- Public Network 호스트 이름 해석 검증
- Private Network 호스트 이름 해석 검증
- VIP 호스트 이름 해석 검증
- SCAN 호스트 이름 해석 검증

**사용 방법**:

```bash
# VM에서 직접 실행
vagrant ssh node1 -c "sudo bash /vagrant/tests/verify_hosts.sh"
vagrant ssh node2 -c "sudo bash /vagrant/tests/verify_hosts.sh"

# 또는 VM 내부에서
sudo bash /vagrant/tests/verify_hosts.sh
```

**검증되는 호스트 이름**:

| 호스트 이름 | 예상 IP | 네트워크 타입 |
|------------|---------|--------------|
| node1.localdomain | 192.168.1.101 | Public |
| node2.localdomain | 192.168.1.102 | Public |
| node1-priv.localdomain | 10.0.0.101 | Private |
| node2-priv.localdomain | 10.0.0.102 | Private |
| node1-vip.localdomain | 192.168.1.111 | VIP |
| node2-vip.localdomain | 192.168.1.112 | VIP |
| rac-scan.localdomain | 192.168.1.121 | SCAN |

**출력 예시**:

```
[INFO] ==========================================
[INFO] /etc/hosts Configuration Verification
[INFO] ==========================================

[INFO] Testing Public Network Hostnames...
[INFO] Testing: node1.localdomain -> 192.168.1.101
[SUCCESS] ✓ node1.localdomain -> 192.168.1.101
[INFO] Testing: node2.localdomain -> 192.168.1.102
[SUCCESS] ✓ node2.localdomain -> 192.168.1.102

[INFO] Testing Private Network Hostnames...
[INFO] Testing: node1-priv.localdomain -> 10.0.0.101
[SUCCESS] ✓ node1-priv.localdomain -> 10.0.0.101
[INFO] Testing: node2-priv.localdomain -> 10.0.0.102
[SUCCESS] ✓ node2-priv.localdomain -> 10.0.0.102

[INFO] Testing VIP Hostnames...
[INFO] Testing: node1-vip.localdomain -> 192.168.1.111
[SUCCESS] ✓ node1-vip.localdomain -> 192.168.1.111
[INFO] Testing: node2-vip.localdomain -> 192.168.1.112
[SUCCESS] ✓ node2-vip.localdomain -> 192.168.1.112

[INFO] Testing SCAN Hostname...
[INFO] Testing: rac-scan.localdomain -> 192.168.1.121
[SUCCESS] ✓ rac-scan.localdomain -> 192.168.1.121

[INFO] ==========================================
[INFO] Test Results Summary
[INFO] ==========================================
[INFO] Total Tests:  7
[SUCCESS] Passed:       7
[INFO] Failed:       0
[INFO] ==========================================
[SUCCESS] All /etc/hosts configuration tests passed!
```

**참고사항**:
- 이 스크립트는 setup_hosts.sh 실행 후에 사용해야 합니다
- getent 명령을 사용하여 호스트 이름 해석을 테스트합니다
- 모든 테스트가 통과하면 exit code 0을 반환합니다
- 테스트 실패 시 exit code 1을 반환합니다
