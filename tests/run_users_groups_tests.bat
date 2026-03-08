@echo off
REM Test runner for Oracle Users/Groups/Directories property-based tests
REM This script runs the property-based tests for Oracle users, groups, and directories configuration

setlocal enabledelayedexpansion

echo ==========================================
echo Oracle Users/Groups/Directories Tests
echo ==========================================
echo.

REM Check if pytest is installed
where pytest >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pytest is not installed
    echo Please install it with: pip install -r requirements.txt
    exit /b 1
)

REM Check if VMs are running
echo Checking if VMs are running...
cd ..
vagrant status | findstr /C:"running" >nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: VMs are not running
    echo Please start VMs with: vagrant up
    exit /b 1
)
cd tests

echo VMs are running. Starting tests...
echo.

REM Run unit tests first (fast)
echo ==========================================
echo Running Unit Tests...
echo ==========================================
pytest test_oracle_users_groups_properties.py -v -m unit --tb=short

echo.
echo ==========================================
echo Running Property-Based Tests (100 examples each)...
echo ==========================================
echo WARNING: Property-based tests may take several minutes to complete
echo.

REM Run property tests with statistics
pytest test_oracle_users_groups_properties.py -v -m property --tb=short --hypothesis-show-statistics

echo.
echo ==========================================
echo All Tests Complete!
echo ==========================================

endlocal
