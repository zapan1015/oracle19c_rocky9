@echo off
REM DNS Configuration Property-Based Tests Runner
REM Oracle 19c RAC 2-Node Cluster Setup
REM
REM This script runs DNS configuration validation tests from Windows host
REM Tests execute commands inside Linux VMs via vagrant ssh

echo ========================================
echo DNS Configuration Tests
echo ========================================
echo.

REM Check if VMs are running
echo Checking VM status...
vagrant status | findstr "running" >nul
if %errorlevel% neq 0 (
    echo [WARNING] VMs are not running. Some tests will be skipped.
    echo Run 'vagrant up' to start VMs before running tests.
    echo.
)

REM Check if dnsmasq is configured
echo Checking DNS configuration...
vagrant ssh node2 -c "systemctl is-active dnsmasq" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] dnsmasq is not running on node2.
    echo Run 'vagrant ssh node2 -c "sudo bash /vagrant/scripts/setup_dnsmasq.sh"' to configure DNS.
    echo.
)

echo Running DNS property-based tests...
echo.

REM Run tests
python -m pytest tests/test_dns_properties.py -v --tb=short

echo.
echo ========================================
echo Test execution completed
echo ========================================

pause
