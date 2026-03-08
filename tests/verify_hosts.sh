#!/bin/bash
#
# /etc/hosts 구성 검증 스크립트
# Oracle RAC 노드의 호스트 이름 해석 테스트
#
# 실행 위치: 모든 노드 (node1, node2)
# 요구사항: 3.6, 3.7, 3.8, 3.9
#

set -e  # 에러 발생 시 즉시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 테스트 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 호스트 이름 해석 테스트 함수
test_hostname_resolution() {
    local hostname=$1
    local expected_ip=$2
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    log_info "Testing: ${hostname} -> ${expected_ip}"
    
    # getent를 사용하여 호스트 이름 해석
    result=$(getent hosts "${hostname}" | awk '{print $1}' | head -1)
    
    if [[ -z "${result}" ]]; then
        log_error "✗ ${hostname} resolution failed (no result)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    if [[ "${result}" == "${expected_ip}" ]]; then
        log_success "✓ ${hostname} -> ${result}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ ${hostname} -> ${result} (expected: ${expected_ip})"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

log_info "=========================================="
log_info "/etc/hosts Configuration Verification"
log_info "=========================================="
echo ""

# Public Network 호스트 검증
log_info "Testing Public Network Hostnames..."
test_hostname_resolution "node1.localdomain" "192.168.1.101"
test_hostname_resolution "node2.localdomain" "192.168.1.102"
echo ""

# Private Network 호스트 검증
log_info "Testing Private Network Hostnames..."
test_hostname_resolution "node1-priv.localdomain" "10.0.0.101"
test_hostname_resolution "node2-priv.localdomain" "10.0.0.102"
echo ""

# VIP 검증
log_info "Testing VIP Hostnames..."
test_hostname_resolution "node1-vip.localdomain" "192.168.1.111"
test_hostname_resolution "node2-vip.localdomain" "192.168.1.112"
echo ""

# SCAN 검증
log_info "Testing SCAN Hostname..."
test_hostname_resolution "rac-scan.localdomain" "192.168.1.121"
echo ""

# 결과 요약
log_info "=========================================="
log_info "Test Results Summary"
log_info "=========================================="
log_info "Total Tests:  ${TOTAL_TESTS}"
log_success "Passed:       ${PASSED_TESTS}"
if [[ ${FAILED_TESTS} -gt 0 ]]; then
    log_error "Failed:       ${FAILED_TESTS}"
else
    log_info "Failed:       ${FAILED_TESTS}"
fi
log_info "=========================================="

if [[ ${FAILED_TESTS} -eq 0 ]]; then
    log_success "All /etc/hosts configuration tests passed!"
    exit 0
else
    log_error "Some /etc/hosts configuration tests failed!"
    exit 1
fi
