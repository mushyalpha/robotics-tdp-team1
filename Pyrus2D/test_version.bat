@echo off
REM Test a specific decision tree version
REM Usage: test_version.bat v1_basic

if "%1"=="" (
    echo Usage: test_version.bat [version]
    echo Versions: v1_basic, v2_positioning, v3_passing, v4_shooting, v5_full
    exit /b 1
)

set VERSION=%1
set WSL_IP=172.28.57.9

echo.
echo ========================================
echo Testing Decision Tree Version: %VERSION%
echo ========================================
echo.

REM Backup current decision.py
if not exist base\decision_backup.py (
    copy base\decision.py base\decision_backup.py
)

REM Copy the version to test
if "%VERSION%"=="v5_full" (
    copy base\decision_backup.py base\decision.py
) else (
    copy base\decision_%VERSION%.py base\decision.py
)

echo Starting team with %VERSION% decision tree...
echo Press Ctrl+C to stop
echo.

REM Start the team
echo Starting goalie...
start /B python main.py --goalie --host %WSL_IP%
timeout /t 1 /nobreak >nul

for /L %%i in (2,1,11) do (
    echo Starting player %%i...
    start /B python main.py --player --host %WSL_IP%
    timeout /t 1 /nobreak >nul
)

timeout /t 2 /nobreak >nul
echo Starting coach...
start /B python main.py --coach --host %WSL_IP%

echo.
echo Team started! Watch the game in rcssmonitor
echo Logs will be saved in logs/ folder
echo.
echo When done, press any key to restore original decision.py
pause

REM Restore original
copy base\decision_backup.py base\decision.py
echo Original decision.py restored
