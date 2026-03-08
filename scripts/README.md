# Scripts Directory

이 디렉토리는 Oracle RAC Vagrant 환경 설정을 위한 스크립트를 포함합니다.

## setup_dnsmasq.sh

**목적**: node2에 dnsmasq DNS 서버를 설치하고 구성합니다.

**요구사항**: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9

**기능**:
- dnsmasq 패키지 설치
- SCAN 이름 해석 구성 (rac-scan.localdomain → 192.168.1.121-123)
- VIP 및 호스트 이름 해석 구성
- 라운드 로빈 DNS 구성
- dnsmasq 서비스 활성화 및 시작
- DNS 해석 테스트 수행

**사용 방법**:

```bash
# node2에서 root 권한으로 실행
sudo bash scripts/setup_dnsmasq.sh
```

**구성되는 DNS 레코드**:

| 호스트 이름 | IP 주소 | 용도 |
|------------|---------|------|
| node1.localdomain | 192.168.1.101 | node1 Public IP |
| node2.localdomain | 192.168.1.102 | node2 Public IP |
| node1-priv.localdomain | 10.0.0.101 | node1 Private IP |
| node2-priv.localdomain | 10.0.0.102 | node2 Private IP |
| node1-vip.localdomain | 192.168.1.111 | node1 VIP |
| node2-vip.localdomain | 192.168.1.112 | node2 VIP |
| rac-scan.localdomain | 192.168.1.121 | SCAN IP 1 |
| rac-scan.localdomain | 192.168.1.122 | SCAN IP 2 |
| rac-scan.localdomain | 192.168.1.123 | SCAN IP 3 |

**검증**:

스크립트는 자동으로 DNS 해석을 테스트합니다. 수동으로 확인하려면:

```bash
# 특정 호스트 이름 테스트
nslookup node1.localdomain 127.0.0.1
nslookup rac-scan.localdomain 127.0.0.1

# SCAN 라운드 로빈 확인 (여러 번 실행)
for i in {1..5}; do nslookup rac-scan.localdomain 127.0.0.1 | grep Address; done
```

**로그 확인**:

```bash
# dnsmasq 서비스 상태
systemctl status dnsmasq

# dnsmasq 로그
tail -f /var/log/dnsmasq.log
```

**다른 노드에서 DNS 서버 사용**:

node1에서 이 DNS 서버를 사용하려면:

```bash
# 임시 설정
echo "nameserver 192.168.1.102" > /etc/resolv.conf

# 영구 설정 (NetworkManager 사용)
nmcli con mod "System eth0" ipv4.dns "192.168.1.102"
nmcli con up "System eth0"
```

**문제 해결**:

1. **dnsmasq 서비스가 시작되지 않는 경우**:
   ```bash
   # 구성 파일 검증
   dnsmasq --test
   
   # 상세 로그 확인
   journalctl -u dnsmasq -xe
   ```

2. **DNS 해석이 작동하지 않는 경우**:
   ```bash
   # dnsmasq가 올바른 인터페이스에서 수신 대기하는지 확인
   ss -tulpn | grep :53
   
   # 방화벽 확인
   firewall-cmd --list-services
   ```

3. **SCAN 라운드 로빈이 작동하지 않는 경우**:
   - dnsmasq는 여러 address 항목을 자동으로 라운드 로빈으로 처리합니다
   - /etc/dnsmasq.conf에서 SCAN 항목이 3개 모두 있는지 확인하세요

**참고사항**:

- 이 스크립트는 멱등성을 보장합니다 (여러 번 실행 가능)
- 기존 dnsmasq 구성은 /etc/dnsmasq.conf.orig로 백업됩니다
- 스크립트는 Rocky Linux 9에서 테스트되었습니다


---

## setup_hosts.sh

**목적**: 모든 노드의 /etc/hosts 파일을 구성합니다.

**요구사항**: 3.6, 3.7, 3.8, 3.9

**기능**:
- /etc/hosts 파일에 Oracle RAC 호스트 엔트리 추가
- Public 및 Private 네트워크 호스트 이름 매핑
- VIP 및 SCAN 호스트 이름 매핑
- 멱등성 보장 (여러 번 실행 가능)
- 기존 파일 백업 (/etc/hosts.orig)

**사용 방법**:

```bash
# Vagrant 프로비저닝 중 자동 실행됨
vagrant up

# 또는 수동으로 각 노드에서 실행
vagrant ssh node1 -c "sudo bash /vagrant/scripts/setup_hosts.sh"
vagrant ssh node2 -c "sudo bash /vagrant/scripts/setup_hosts.sh"
```

**구성되는 호스트 엔트리**:

```
# Public Network - Node hostnames
192.168.1.101   node1.localdomain       node1
192.168.1.102   node2.localdomain       node2

# Private Network - Node hostnames (Interconnect)
10.0.0.101      node1-priv.localdomain  node1-priv
10.0.0.102      node2-priv.localdomain  node2-priv

# Virtual IP (VIP) addresses
192.168.1.111   node1-vip.localdomain   node1-vip
192.168.1.112   node2-vip.localdomain   node2-vip

# SCAN addresses (Single Client Access Name)
192.168.1.121   rac-scan.localdomain    rac-scan
192.168.1.122   rac-scan.localdomain    rac-scan
192.168.1.123   rac-scan.localdomain    rac-scan
```

**검증**:

스크립트는 자동으로 호스트 이름 해석을 검증합니다. 수동으로 확인하려면:

```bash
# 특정 호스트 이름 테스트
getent hosts node1.localdomain
getent hosts node1-priv.localdomain
getent hosts rac-scan.localdomain

# 또는 검증 스크립트 사용
sudo bash /vagrant/tests/verify_hosts.sh
```

**멱등성**:

이 스크립트는 여러 번 실행해도 안전합니다:
- 기존 Oracle RAC 섹션을 자동으로 제거
- 새로운 엔트리로 교체
- 원본 파일은 .orig 확장자로 한 번만 백업

**참고사항**:

- /etc/hosts의 SCAN 엔트리는 DNS 장애 시 폴백용입니다
- 프로덕션 환경에서는 DNS 서버(dnsmasq)를 사용하는 것이 권장됩니다
- DNS를 사용하면 SCAN 라운드 로빈이 제대로 작동합니다
- 이 스크립트는 Rocky Linux 9에서 테스트되었습니다

**Vagrant 통합**:

Vagrantfile에서 자동으로 실행되도록 구성되어 있습니다:

```ruby
config.vm.define "node1" do |node1|
  node1.vm.provision "shell", path: "scripts/setup_hosts.sh"
end

config.vm.define "node2" do |node2|
  node2.vm.provision "shell", path: "scripts/setup_hosts.sh"
end
```

**문제 해결**:

1. **호스트 이름 해석 실패**:
   ```bash
   # /etc/hosts 파일 확인
   cat /etc/hosts
   
   # Oracle RAC 섹션이 있는지 확인
   grep "Oracle RAC Hosts" /etc/hosts
   ```

2. **스크립트 재실행**:
   ```bash
   # 기존 구성 제거하고 재실행
   sudo bash /vagrant/scripts/setup_hosts.sh
   ```

3. **백업 파일 복원**:
   ```bash
   # 원본 파일로 복원
   sudo cp /etc/hosts.orig /etc/hosts
   ```
